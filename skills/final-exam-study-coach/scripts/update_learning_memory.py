#!/usr/bin/env python3
"""Update a learner memory database for the study assistant skill."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


KIND_TO_BUCKET = {
    "wrong": "wrong_questions",
    "doubt": "doubts",
    "homework": "homework_reviews",
    "mastery": "mastery_updates",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def local_date(offset_days: int = 0) -> str:
    return (datetime.now().date() + timedelta(days=offset_days)).isoformat()


def load_db(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": "learning-assistant-memory-v1",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "courses": {},
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("version", "learning-assistant-memory-v1")
    data.setdefault("courses", {})
    return data


def course_entry(db: dict[str, Any], course: str) -> dict[str, Any]:
    courses = db.setdefault("courses", {})
    entry = courses.setdefault(
        course,
        {
            "wrong_questions": [],
            "doubts": [],
            "homework_reviews": [],
            "mastery_updates": [],
            "concept_stats": {},
        },
    )
    entry.setdefault("concept_stats", {})
    for bucket in KIND_TO_BUCKET.values():
        entry.setdefault(bucket, [])
    return entry


def next_review_date(kind: str, confidence: int | None) -> str:
    if kind == "wrong":
        return local_date(1 if confidence is None or confidence <= 2 else 3)
    if kind == "doubt":
        return local_date(1)
    if kind == "homework":
        return local_date(3)
    return local_date(7)


def make_record(args: argparse.Namespace) -> dict[str, Any]:
    record = {
        "id": f"{args.kind}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "created_at": now_iso(),
        "course": args.course,
        "concept": args.concept,
        "kind": args.kind,
        "prompt": args.prompt or "",
        "student_answer": args.student_answer or "",
        "correct_answer": args.correct_answer or "",
        "error_type": args.error_type or "",
        "fix_rule": args.fix_rule or "",
        "source": args.source or "",
        "confidence": args.confidence,
        "resolved": args.resolved,
        "next_review": args.next_review or next_review_date(args.kind, args.confidence),
        "tags": [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()],
    }
    if args.image:
        record["image"] = args.image
    if args.annotated_image:
        record["annotated_image"] = args.annotated_image
    return record


def update_concept_stats(course: dict[str, Any], record: dict[str, Any]) -> None:
    concept = record["concept"]
    stats = course.setdefault("concept_stats", {}).setdefault(
        concept,
        {
            "wrong_count": 0,
            "doubt_count": 0,
            "homework_review_count": 0,
            "mastery_update_count": 0,
            "last_seen": "",
            "latest_confidence": None,
            "next_review": "",
            "common_error_types": {},
        },
    )
    if record["kind"] == "wrong":
        stats["wrong_count"] += 1
    elif record["kind"] == "doubt":
        stats["doubt_count"] += 1
    elif record["kind"] == "homework":
        stats["homework_review_count"] += 1
    elif record["kind"] == "mastery":
        stats["mastery_update_count"] = stats.get("mastery_update_count", 0) + 1
    stats["last_seen"] = record["created_at"]
    stats["latest_confidence"] = record.get("confidence")
    stats["next_review"] = record.get("next_review", "")
    error_type = record.get("error_type")
    if error_type:
        errors = Counter(stats.get("common_error_types", {}))
        errors[error_type] += 1
        stats["common_error_types"] = dict(errors.most_common())


def write_markdown(db: dict[str, Any], path: Path) -> None:
    lines = ["# 学习记忆库摘要", "", f"- 更新时间: {db.get('updated_at', '')}", ""]
    for course_name, course in db.get("courses", {}).items():
        lines.extend([f"## {course_name}", ""])
        stats = course.get("concept_stats", {})
        if stats:
            lines.append("| 知识点 | 错题 | 疑问 | 作业批改 | 掌握记录 | 最近置信度 | 下次复习 |")
            lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- |")
            for concept, item in sorted(stats.items()):
                lines.append(
                    "| {concept} | {wrong} | {doubt} | {homework} | {mastery} | {confidence} | {review} |".format(
                        concept=concept,
                        wrong=item.get("wrong_count", 0),
                        doubt=item.get("doubt_count", 0),
                        homework=item.get("homework_review_count", 0),
                        mastery=item.get("mastery_update_count", 0),
                        confidence=item.get("latest_confidence", ""),
                        review=item.get("next_review", ""),
                    )
                )
            lines.append("")
        for bucket, title in [
            ("wrong_questions", "最近错题"),
            ("doubts", "最近疑问"),
            ("homework_reviews", "最近作业批改"),
            ("mastery_updates", "最近掌握度记录"),
        ]:
            records = course.get(bucket, [])[-5:]
            if records:
                lines.extend([f"### {title}", ""])
                for record in records:
                    lines.append(
                        f"- {record.get('concept', '')}: {record.get('fix_rule') or record.get('prompt', '')} "
                        f"(下次复习: {record.get('next_review', '')})"
                    )
                lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_checkpoint(db: dict[str, Any], path: Path) -> None:
    checkpoint = {
        "updated_at": db.get("updated_at"),
        "courses": {},
        "resume_rule": "上下文压缩后先读取 learning_memory.json 和 learning_memory_checkpoint.json，再继续带学、批改或生成考前复习页。",
    }
    for course_name, course in db.get("courses", {}).items():
        stats = course.get("concept_stats", {})
        weakest = sorted(
            stats.items(),
            key=lambda kv: (
                kv[1].get("latest_confidence") if kv[1].get("latest_confidence") is not None else 99,
                -kv[1].get("wrong_count", 0),
                -kv[1].get("doubt_count", 0),
            ),
        )[:5]
        checkpoint["courses"][course_name] = {
            "wrong_total": len(course.get("wrong_questions", [])),
            "doubt_total": len(course.get("doubts", [])),
            "homework_review_total": len(course.get("homework_reviews", [])),
            "mastery_update_total": len(course.get("mastery_updates", [])),
            "priority_concepts": [name for name, _ in weakest],
        }
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update learner memory for review, homework correction, and doubt tracking.")
    parser.add_argument("database", type=Path)
    parser.add_argument("--record-json", type=Path, help="UTF-8 JSON file with record fields; avoids shell encoding issues.")
    parser.add_argument("--course")
    parser.add_argument("--concept")
    parser.add_argument("--kind", choices=sorted(KIND_TO_BUCKET))
    parser.add_argument("--prompt", default="")
    parser.add_argument("--student-answer", default="")
    parser.add_argument("--correct-answer", default="")
    parser.add_argument("--error-type", default="")
    parser.add_argument("--fix-rule", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--confidence", type=int, choices=range(1, 6))
    parser.add_argument("--next-review", default="")
    parser.add_argument("--tags", default="")
    parser.add_argument("--image", default="")
    parser.add_argument("--annotated-image", default="")
    parser.add_argument("--resolved", action="store_true")
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()

    if args.record_json:
        payload = json.loads(args.record_json.read_text(encoding="utf-8"))
        for key, value in payload.items():
            attr = key.replace("-", "_")
            if hasattr(args, attr):
                setattr(args, attr, value)
    missing = [name for name in ("course", "concept", "kind") if not getattr(args, name)]
    if missing:
        parser.error("missing required fields: " + ", ".join(missing))

    db = load_db(args.database)
    db["updated_at"] = now_iso()
    course = course_entry(db, args.course)
    record = make_record(args)
    course[KIND_TO_BUCKET[args.kind]].append(record)
    update_concept_stats(course, record)

    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.database.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

    markdown_path = args.markdown or args.database.with_suffix(".md")
    checkpoint_path = args.checkpoint or args.database.with_name(args.database.stem + "_checkpoint.json")
    write_markdown(db, markdown_path)
    write_checkpoint(db, checkpoint_path)
    print(f"updated {args.database}")
    print(f"summary {markdown_path}")
    print(f"checkpoint {checkpoint_path}")


if __name__ == "__main__":
    main()
