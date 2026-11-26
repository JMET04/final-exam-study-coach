#!/usr/bin/env python3
"""Build an anonymized teacher-facing progress report from learner memory."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_db(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_course(db: dict[str, Any], course_name: str | None) -> list[tuple[str, dict[str, Any]]]:
    courses = db.get("courses", {})
    if course_name:
        return [(course_name, courses.get(course_name, {}))]
    return list(courses.items())


def top_counter(records: list[dict[str, Any]], field: str, limit: int = 5) -> list[tuple[str, int]]:
    counter = Counter(str(record.get(field, "")).strip() for record in records if str(record.get(field, "")).strip())
    return counter.most_common(limit)


def report_for_course(name: str, course: dict[str, Any], privacy: str) -> list[str]:
    wrong = course.get("wrong_questions", [])
    doubts = course.get("doubts", [])
    homework = course.get("homework_reviews", [])
    stats = course.get("concept_stats", {})
    lines = [
        f"## {name}",
        "",
        f"- 隐私模式：{privacy}",
        f"- 错题记录：{len(wrong)}",
        f"- 疑问记录：{len(doubts)}",
        f"- 作业批改记录：{len(homework)}",
        "",
    ]
    if stats:
        weak = sorted(stats.items(), key=lambda kv: (kv[1].get("latest_confidence") or 0, -kv[1].get("wrong_count", 0)))[:5]
        lines.extend(["### 掌握度薄弱点", "", "| 知识点 | 错题 | 疑问 | 最近置信度 | 建议动作 |", "| --- | ---: | ---: | --- | --- |"])
        for concept, item in weak:
            lines.append(f"| {concept} | {item.get('wrong_count', 0)} | {item.get('doubt_count', 0)} | {item.get('latest_confidence', '')} | 下节课或答疑课用5-10分钟回讲，并配一道变式题 |")
        lines.append("")

    lines.extend(["### 高频错因 TOP 5", ""])
    error_items = top_counter(wrong + homework, "error_type")
    lines.extend([f"- {label}：{count} 次" for label, count in error_items] or ["- 暂无足够数据"])
    lines.extend(["", "### 未解决疑问 TOP 5", ""])
    unresolved = [item for item in doubts if not item.get("resolved")]
    doubt_items = top_counter(unresolved, "concept")
    lines.extend([f"- {label}：{count} 次" for label, count in doubt_items] or ["- 暂无未解决疑问"])
    lines.extend(
        [
            "",
            "### 教学建议",
            "",
            "- 课前：给薄弱知识点安排10-20分钟预习卡，先补最短前置概念。",
            "- 课中：优先回讲高频错因对应步骤，不只重复定义。",
            "- 课后：按错因分层布置练习，基础层做典型题，提升层做变式题。",
            "",
        ]
    )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Create teacher progress report from learner memory.")
    parser.add_argument("database", type=Path)
    parser.add_argument("--course")
    parser.add_argument("--privacy", choices=["anonymous", "named"], default="anonymous")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    db = load_db(args.database)
    lines = [
        "# 教师课程进度与学习问题报告",
        "",
        f"- 生成时间：{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 数据来源：学习记忆库中的错题、疑问、作业批改和掌握度记录。",
        "- 默认只做教学改进建议，不包含学生原始照片或私密聊天内容。",
        "",
    ]
    for course_name, course in collect_course(db, args.course):
        lines.extend(report_for_course(course_name, course, args.privacy))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
