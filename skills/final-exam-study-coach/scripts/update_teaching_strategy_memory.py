#!/usr/bin/env python3
"""Record and recommend teaching strategies for the learning assistant."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESULT_SCORE = {"understood": 2.0, "partial": 0.8, "confused": -1.0}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_db(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": "teaching-strategy-memory-v1", "created_at": now_iso(), "updated_at": now_iso(), "episodes": [], "strategy_stats": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("episodes", [])
    data.setdefault("strategy_stats", {})
    return data


def split_tags(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).replace("；", ",").replace("，", ",").split(",") if item.strip()]


def profile_signature(tags: list[str]) -> str:
    return "|".join(sorted(set(tags))) if tags else "unspecified"


def stat_key(course: str, concept: str, profile_tags: list[str], strategy: str) -> str:
    return "||".join([course, concept, profile_signature(profile_tags), strategy])


def score_episode(record: dict[str, Any]) -> float:
    before = record.get("before_confidence")
    after = record.get("after_confidence")
    gain = after - before if isinstance(before, int) and isinstance(after, int) else 0.0
    return gain + RESULT_SCORE.get(str(record.get("result", "partial")), 0.0)


def normalize_record(payload: dict[str, Any]) -> dict[str, Any]:
    required = ["course", "concept", "student_profile", "teaching_strategy", "result"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise SystemExit("missing required fields in record json: " + ", ".join(missing))
    return {
        "id": payload.get("id") or f"teach-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "created_at": now_iso(),
        "course": str(payload["course"]),
        "concept": str(payload["concept"]),
        "topic_type": str(payload.get("topic_type", "")),
        "student_profile": str(payload["student_profile"]),
        "profile_tags": split_tags(payload.get("profile_tags") or payload.get("student_profile")),
        "student_question": str(payload.get("student_question", "")),
        "teaching_strategy": str(payload["teaching_strategy"]),
        "explanation_summary": str(payload.get("explanation_summary", "")),
        "example_used": str(payload.get("example_used", "")),
        "understanding_evidence": str(payload.get("understanding_evidence", "")),
        "before_confidence": payload.get("before_confidence"),
        "after_confidence": payload.get("after_confidence"),
        "student_feedback": str(payload.get("student_feedback", "")),
        "result": str(payload["result"]),
        "next_strategy": str(payload.get("next_strategy", "")),
        "privacy_note": "Only learning-behavior profile is stored; no private identity is required.",
    }


def update_stats(db: dict[str, Any], record: dict[str, Any]) -> None:
    key = stat_key(record["course"], record["concept"], record["profile_tags"], record["teaching_strategy"])
    stats = db.setdefault("strategy_stats", {}).setdefault(
        key,
        {"course": record["course"], "concept": record["concept"], "profile_signature": profile_signature(record["profile_tags"]), "teaching_strategy": record["teaching_strategy"], "count": 0, "success_count": 0, "partial_count": 0, "confused_count": 0, "total_score": 0.0, "average_score": 0.0, "latest_evidence": "", "last_seen": ""},
    )
    stats["count"] += 1
    if record["result"] == "understood":
        stats["success_count"] += 1
    elif record["result"] == "confused":
        stats["confused_count"] += 1
    else:
        stats["partial_count"] += 1
    stats["total_score"] += score_episode(record)
    stats["average_score"] = round(stats["total_score"] / stats["count"], 3)
    stats["latest_evidence"] = record.get("understanding_evidence", "")
    stats["last_seen"] = record["created_at"]


def write_markdown(db: dict[str, Any], path: Path) -> None:
    lines = ["# 讲解策略记忆库摘要", "", f"- 更新时间：{db.get('updated_at', '')}", ""]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for stats in db.get("strategy_stats", {}).values():
        grouped[(stats["course"], stats["concept"])].append(stats)
    for (course, concept), items in sorted(grouped.items()):
        lines.extend([f"## {course} / {concept}", "", "| 学生画像 | 讲法 | 次数 | 平均效果 | 成功 | 困惑 | 最新证据 |", "| --- | --- | ---: | ---: | ---: | ---: | --- |"])
        for item in sorted(items, key=lambda item: (-item["average_score"], -item["count"])):
            lines.append(f"| {item['profile_signature']} | {item['teaching_strategy']} | {item['count']} | {item['average_score']} | {item['success_count']} | {item['confused_count']} | {item.get('latest_evidence', '')} |")
        lines.append("")
    if len(lines) == 3:
        lines.append("暂无讲解策略记录。")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def record_case(args: argparse.Namespace) -> None:
    db = load_db(args.database)
    record = normalize_record(json.loads(args.record_json.read_text(encoding="utf-8")))
    db["episodes"].append(record)
    update_stats(db, record)
    db["updated_at"] = now_iso()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.database.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = args.markdown or args.database.with_suffix(".md")
    write_markdown(db, summary_path)
    print(f"updated {args.database}")
    print(f"summary {summary_path}")


def overlap_score(query_tags: list[str], stats: dict[str, Any]) -> int:
    if not query_tags:
        return 0
    return len(set(query_tags) & set(str(stats.get("profile_signature", "")).split("|")))


def recommend(args: argparse.Namespace) -> None:
    db = load_db(args.database)
    if args.query_json:
        payload = json.loads(args.query_json.read_text(encoding="utf-8"))
        for key, value in payload.items():
            attr = key.replace("-", "_")
            if hasattr(args, attr):
                setattr(args, attr, value)
    query_tags = split_tags(args.student_profile)
    candidates = []
    for stats in db.get("strategy_stats", {}).values():
        if args.course and stats.get("course") != args.course:
            continue
        if args.concept and stats.get("concept") != args.concept:
            continue
        score = float(stats.get("average_score", 0)) + overlap_score(query_tags, stats) * 0.3 + min(int(stats.get("count", 0)), 5) * 0.05
        candidates.append((score, stats))
    candidates.sort(key=lambda item: item[0], reverse=True)
    lines = ["# 讲解策略推荐", "", f"- 课程：{args.course or '未限定'}", f"- 知识点：{args.concept or '未限定'}", f"- 学生画像：{args.student_profile or '未提供'}", ""]
    if not candidates:
        lines.append("暂无足够历史记录。建议先用最小讲解循环：短讲解 -> 复述 -> 1道小测 -> 记录效果。")
    else:
        lines.extend(["| 推荐顺序 | 讲法 | 历史画像 | 次数 | 平均效果 | 最新证据 |", "| ---: | --- | --- | ---: | ---: | --- |"])
        for index, (_, stats) in enumerate(candidates[: args.limit], start=1):
            lines.append(f"| {index} | {stats['teaching_strategy']} | {stats['profile_signature']} | {stats['count']} | {stats['average_score']} | {stats.get('latest_evidence', '')} |")
        lines.extend(["", "使用建议：先用排名最高的讲法讲3-5分钟，再让学生复述或做一道变式题；如果仍 confused，换第二种讲法。"])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Record and recommend effective teaching strategies.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("database", type=Path)
    record_parser.add_argument("--record-json", type=Path, required=True)
    record_parser.add_argument("--markdown", type=Path)
    record_parser.set_defaults(func=record_case)
    recommend_parser = subparsers.add_parser("recommend")
    recommend_parser.add_argument("database", type=Path)
    recommend_parser.add_argument("--query-json", type=Path)
    recommend_parser.add_argument("--course", default="")
    recommend_parser.add_argument("--concept", default="")
    recommend_parser.add_argument("--student-profile", default="")
    recommend_parser.add_argument("--limit", type=int, default=3)
    recommend_parser.add_argument("--output", type=Path)
    recommend_parser.set_defaults(func=recommend)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
