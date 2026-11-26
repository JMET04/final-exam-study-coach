#!/usr/bin/env python3
"""Build a pre-exam review page from wrong points and weak familiarity points."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


EMPTY_COURSE = {
    "wrong_questions": [],
    "doubts": [],
    "homework_reviews": [],
    "mastery_updates": [],
    "concept_stats": {},
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None


def course_data(db: dict[str, Any], course: str | None) -> tuple[str, dict[str, Any]]:
    courses = db.get("courses") or {}
    if course and course in courses:
        return course, courses[course]
    if course:
        return course, dict(EMPTY_COURSE)
    if not courses:
        return "未命名课程", dict(EMPTY_COURSE)
    first = next(iter(courses))
    return first, courses[first]


def recency_boost(record: dict[str, Any], exam_day: date | None) -> float:
    next_review = parse_date(str(record.get("next_review") or ""))
    if not exam_day or not next_review:
        return 0.0
    days = (exam_day - next_review).days
    if days < 0:
        return 0.0
    return max(0, 7 - min(days, 7)) * 0.25


def confidence_penalty(confidence: Any) -> float:
    if isinstance(confidence, int):
        return max(0, 5 - confidence) * 0.9
    return 1.0


def wrong_record_score(record: dict[str, Any], exam_day: date | None) -> float:
    score = 1.0 + confidence_penalty(record.get("confidence")) + recency_boost(record, exam_day)
    if not record.get("resolved"):
        score += 1.2
    if record.get("error_type"):
        score += 0.5
    if record.get("fix_rule"):
        score += 0.4
    return score


def weak_record_score(record: dict[str, Any], exam_day: date | None) -> float:
    score = 0.8 + confidence_penalty(record.get("confidence")) + recency_boost(record, exam_day)
    if not record.get("resolved"):
        score += 0.8
    if record.get("kind") == "doubt":
        score += 0.6
    return score


def collect_wrong_points(course: dict[str, Any], exam_day: date | None, limit: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for bucket in ("wrong_questions", "homework_reviews"):
        for record in course.get(bucket, []):
            item = dict(record)
            item["source_bucket"] = bucket
            concept = str(item.get("concept") or "未标注知识点")
            error_type = str(item.get("error_type") or "未标注错因")
            grouped[(concept, error_type)].append(item)

    points = []
    for (concept, error_type), items in grouped.items():
        ranked = sorted(items, key=lambda item: wrong_record_score(item, exam_day), reverse=True)
        fix_rules = Counter(str(item.get("fix_rule") or "") for item in items if item.get("fix_rule"))
        confidences = [item.get("confidence") for item in items if isinstance(item.get("confidence"), int)]
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else None
        fix_rule = fix_rules.most_common(1)[0][0] if fix_rules else "先写定义/公式/适用条件，再进入计算或判断。"
        score = sum(wrong_record_score(item, exam_day) for item in items) + len(items) * 0.8
        typical = ranked[0] if ranked else {}
        points.append(
            {
                "concept": concept,
                "error_type": error_type,
                "count": len(items),
                "avg_confidence": avg_confidence,
                "priority_score": round(score, 2),
                "fix_rule": fix_rule,
                "typical_prompt": typical.get("prompt", ""),
                "student_answer": typical.get("student_answer", ""),
                "correct_answer": typical.get("correct_answer", ""),
                "quick_check": f"闭卷写出{concept}的关键规则，并说清为什么不能按“{error_type}”处理。",
            }
        )
    points.sort(key=lambda item: item["priority_score"], reverse=True)
    return points[:limit]


def collect_weak_points(course: dict[str, Any], exam_day: date | None, limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for bucket in ("doubts", "mastery_updates"):
        for record in course.get(bucket, []):
            item = dict(record)
            item["source_bucket"] = bucket
            item["reason"] = "未解决疑问" if bucket == "doubts" else "自评掌握度偏低"
            candidates.append(item)

    for concept, stats in course.get("concept_stats", {}).items():
        confidence = stats.get("latest_confidence")
        has_low_confidence = isinstance(confidence, int) and confidence <= 3
        has_due_review = bool(stats.get("next_review"))
        if has_low_confidence or has_due_review:
            candidates.append(
                {
                    "kind": "concept_stats",
                    "concept": concept,
                    "confidence": confidence,
                    "next_review": stats.get("next_review", ""),
                    "prompt": "",
                    "reason": "概念统计显示低置信度或临近复习",
                    "resolved": False,
                    "wrong_count": stats.get("wrong_count", 0),
                    "doubt_count": stats.get("doubt_count", 0),
                }
            )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        grouped[str(item.get("concept") or "未标注知识点")].append(item)

    weak_points = []
    for concept, items in grouped.items():
        ranked = sorted(items, key=lambda item: weak_record_score(item, exam_day), reverse=True)
        top = ranked[0]
        confidence_values = [item.get("confidence") for item in items if isinstance(item.get("confidence"), int)]
        confidence = min(confidence_values) if confidence_values else top.get("confidence")
        reasons = []
        if any(item.get("source_bucket") == "doubts" for item in items):
            reasons.append("有未解决/反复疑问")
        if isinstance(confidence, int) and confidence <= 3:
            reasons.append(f"置信度{confidence}/5")
        if any(item.get("source_bucket") == "mastery_updates" for item in items):
            reasons.append("用户标记还不熟")
        if any(item.get("kind") == "concept_stats" for item in items):
            reasons.append("学习统计要求复习")
        score = sum(weak_record_score(item, exam_day) for item in items)
        weak_points.append(
            {
                "concept": concept,
                "reason": "；".join(dict.fromkeys(reasons)) or str(top.get("reason") or "需要复习"),
                "confidence": confidence,
                "priority_score": round(score, 2),
                "latest_prompt": top.get("prompt", ""),
                "review_action": f"用费曼法讲清{concept}，再做1道最小题验证是否真会。",
            }
        )
    weak_points.sort(key=lambda item: item["priority_score"], reverse=True)
    return weak_points[:limit]


def build_page(db: dict[str, Any], course_name: str, exam_date: str, limit: int) -> dict[str, Any]:
    selected_course, course = course_data(db, course_name)
    exam_day = parse_date(exam_date)
    wrong_points = collect_wrong_points(course, exam_day, limit)
    weak_points = collect_weak_points(course, exam_day, limit)
    quick_checklist = []
    for item in wrong_points[:5]:
        quick_checklist.append(f"{item['concept']}: {item['fix_rule']}")
    for item in weak_points[:5]:
        quick_checklist.append(f"{item['concept']}: {item['review_action']}")
    return {
        "version": "pre-exam-review-page-v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "course": selected_course,
        "exam_date": exam_date,
        "record_counts": {
            "wrong_questions": len(course.get("wrong_questions", [])),
            "doubts": len(course.get("doubts", [])),
            "homework_reviews": len(course.get("homework_reviews", [])),
            "mastery_updates": len(course.get("mastery_updates", [])),
        },
        "wrong_points": wrong_points,
        "weak_points": weak_points,
        "quick_checklist": quick_checklist[:10],
        "fallback_note": ""
        if wrong_points or weak_points
        else "学习记忆库里暂时没有错题、疑问或低掌握度记录。先做一次诊断小测或录入最近错题，再生成考前复习页。",
    }


def table_cell(value: Any) -> str:
    return str(value or "").replace("\n", " ").replace("|", "｜")


def write_markdown(data: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {data['course']} 考前复习页",
        "",
        f"- 考试日期: {data.get('exam_date') or '未提供'}",
        "- 数据来源: 学习记忆库中的错题、疑问、作业批改、掌握度记录和知识点统计",
        "- 使用方式: 考前先看高频错因，再看不熟点，最后用清单闭卷自测",
        "",
    ]
    counts = data["record_counts"]
    lines.extend(
        [
            "## 数据概览",
            "",
            f"- 错题: {counts['wrong_questions']} 条",
            f"- 疑问: {counts['doubts']} 条",
            f"- 作业批改: {counts['homework_reviews']} 条",
            f"- 掌握度记录: {counts['mastery_updates']} 条",
            "",
        ]
    )
    if data["fallback_note"]:
        lines.append(data["fallback_note"])
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return

    lines.extend(
        [
            "## 一、高频错题/错因",
            "",
            "| 优先级 | 知识点 | 错因 | 次数 | 正确规则 | 1分钟检查 |",
            "| ---: | --- | --- | ---: | --- | --- |",
        ]
    )
    for index, item in enumerate(data["wrong_points"], start=1):
        lines.append(
            "| {idx} | {concept} | {error_type} | {count} | {fix_rule} | {quick_check} |".format(
                idx=index,
                concept=table_cell(item["concept"]),
                error_type=table_cell(item["error_type"]),
                count=item["count"],
                fix_rule=table_cell(item["fix_rule"]),
                quick_check=table_cell(item["quick_check"]),
            )
        )
    if not data["wrong_points"]:
        lines.append("| - | 暂无 | 暂无历史错题 | 0 | 先做诊断题建立记录 | - |")

    lines.extend(
        [
            "",
            "## 二、不熟点/低置信度",
            "",
            "| 优先级 | 知识点 | 为什么要看 | 置信度 | 复习动作 |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for index, item in enumerate(data["weak_points"], start=1):
        lines.append(
            "| {idx} | {concept} | {reason} | {confidence} | {action} |".format(
                idx=index,
                concept=table_cell(item["concept"]),
                reason=table_cell(item["reason"]),
                confidence=table_cell(item["confidence"]),
                action=table_cell(item["review_action"]),
            )
        )
    if not data["weak_points"]:
        lines.append("| - | 暂无 | 暂无疑问或低掌握度记录 | - | 做一次快速自测确认 |")

    lines.extend(["", "## 三、最后15分钟检查清单", ""])
    for item in data["quick_checklist"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 四、考前禁止事项",
            "",
            "- 不要临时铺开整本书；只回到上表中的错因和不熟点。",
            "- 不要只看答案；每个点至少闭卷说出规则或做一道最小题。",
            "- 不要新增大块陌生内容；除非它来自老师明确范围或高频题型。",
            "- 不要熬到影响考试状态；短睡眠比低质量通宵更值钱。",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a pre-exam review page from wrong and weak learner memory.")
    parser.add_argument("database", type=Path)
    parser.add_argument("--course", default="")
    parser.add_argument("--exam-date", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    data = build_page(load_json(args.database), args.course, args.exam_date, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(data, args.output)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.output}")
    if args.json_output:
        print(f"wrote {args.json_output}")


if __name__ == "__main__":
    main()
