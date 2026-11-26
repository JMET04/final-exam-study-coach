#!/usr/bin/env python3
"""Generate pre-exam mistake reminders from the learner memory database."""

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


def collect_records(course: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for bucket in ("wrong_questions", "homework_reviews"):
        for record in course.get(bucket, []):
            item = dict(record)
            item.setdefault("source_bucket", bucket)
            records.append(item)
    return records


def record_score(record: dict[str, Any], exam_day: date | None) -> float:
    score = 1.0
    confidence = record.get("confidence")
    if isinstance(confidence, int):
        score += max(0, 5 - confidence) * 0.8
    if not record.get("resolved"):
        score += 1.2
    if record.get("error_type"):
        score += 0.6
    if record.get("fix_rule"):
        score += 0.4
    next_review = parse_date(str(record.get("next_review") or ""))
    if exam_day and next_review:
        days = (exam_day - next_review).days
        if days >= 0:
            score += max(0, 7 - min(days, 7)) * 0.2
    return score


def build_reminders(db: dict[str, Any], course_name: str, exam_date: str, limit: int) -> dict[str, Any]:
    selected_course, course = course_data(db, course_name)
    exam_day = parse_date(exam_date)
    records = collect_records(course)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        concept = str(record.get("concept") or "未标注知识点")
        error_type = str(record.get("error_type") or "未标注错因")
        grouped[(concept, error_type)].append(record)

    reminders = []
    for (concept, error_type), items in grouped.items():
        ranked = sorted(items, key=lambda item: record_score(item, exam_day), reverse=True)
        fix_rules = Counter(str(item.get("fix_rule") or "") for item in items if item.get("fix_rule"))
        prompts = [str(item.get("prompt") or "") for item in ranked if item.get("prompt")]
        correct_answers = [str(item.get("correct_answer") or "") for item in ranked if item.get("correct_answer")]
        student_answers = [str(item.get("student_answer") or "") for item in ranked if item.get("student_answer")]
        confidence_values = [item.get("confidence") for item in items if isinstance(item.get("confidence"), int)]
        avg_confidence = round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else None
        total_score = sum(record_score(item, exam_day) for item in items) + len(items) * 0.5
        fix_rule = fix_rules.most_common(1)[0][0] if fix_rules else "先写出定义、公式或适用条件，再代入或判断。"
        reminders.append(
            {
                "concept": concept,
                "error_type": error_type,
                "count": len(items),
                "avg_confidence": avg_confidence,
                "priority_score": round(total_score, 2),
                "typical_prompt": prompts[0] if prompts else "",
                "student_answer": student_answers[0] if student_answers else "",
                "correct_answer": correct_answers[0] if correct_answers else "",
                "fix_rule": fix_rule,
                "dont_do": f"不要再按“{error_type}”的旧习惯直接作答。",
                "one_sentence": f"看到{concept}，先提醒自己：{fix_rule}",
                "mini_test": f"闭卷用1分钟写出{concept}的关键规则，再做1道同类小题。",
            }
        )
    reminders.sort(key=lambda item: item["priority_score"], reverse=True)
    reminders = reminders[:limit]
    return {
        "version": "exam-mistake-reminders-v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "course": selected_course,
        "exam_date": exam_date,
        "record_count": len(records),
        "reminders": reminders,
        "fallback_note": "" if reminders else "错题库中暂时没有可用错题。先用诊断小测建立错题记录，再生成考前提醒。",
    }


def write_markdown(data: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {data['course']} 考前易错提醒",
        "",
        f"- 考试日期: {data.get('exam_date') or '未提供'}",
        f"- 已读取错题/作业记录: {data['record_count']} 条",
        "",
    ]
    if data["fallback_note"]:
        lines.append(data["fallback_note"])
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return
    lines.extend(
        [
            "## 考前15分钟先看",
            "",
            "| 优先级 | 知识点 | 错因 | 正确规则 | 不要再这样 | 1分钟自测 |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for index, item in enumerate(data["reminders"], start=1):
        lines.append(
            f"| {index} | {item['concept']} | {item['error_type']} | {item['fix_rule']} | {item['dont_do']} | {item['mini_test']} |"
        )
    lines.extend(["", "## 最后一遍自查清单", ""])
    for item in data["reminders"]:
        lines.append(f"- {item['one_sentence']}")
    lines.extend(["", "## 典型错题回看", ""])
    for item in data["reminders"]:
        prompt = item.get("typical_prompt") or "暂无题面"
        answer = item.get("correct_answer") or "暂无标准答案"
        old_answer = item.get("student_answer") or "暂无原答案"
        lines.append(f"- **{item['concept']}**: {prompt} | 原答: {old_answer} | 正解: {answer}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pre-exam mistake reminders from learner memory.")
    parser.add_argument("database", type=Path)
    parser.add_argument("--course", default="")
    parser.add_argument("--exam-date", default="")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    data = build_reminders(load_json(args.database), args.course, args.exam_date, args.limit)
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
