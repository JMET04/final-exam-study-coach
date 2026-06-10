#!/usr/bin/env python3
"""Update a reusable study-state JSON file after a learning session."""

from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ORDER = ["unknown", "cannot_start", "can_recognize", "can_explain", "can_solve_slowly", "exam_ready"]


def next_status(current: str, result: str, confidence: int) -> str:
    if current not in ORDER:
        current = "unknown"
    idx = ORDER.index(current)
    if result == "missed":
        return current if current != "unknown" else "cannot_start"
    if result == "wrong" or confidence <= 2:
        if current == "unknown":
            return "cannot_start"
        idx = max(0, idx - 1)
        return ORDER[idx]
    if result == "partial" or confidence == 3:
        if current in {"unknown", "cannot_start"}:
            return "can_recognize"
        return current
    if current == "unknown":
        return "can_recognize"
    if current == "cannot_start":
        return "can_explain" if confidence >= 5 else "can_recognize"
    step = 2 if confidence >= 5 and current in {"can_recognize", "can_explain"} else 1
    return ORDER[min(len(ORDER) - 1, idx + step)]


def next_review(confidence: int) -> str:
    days = 1 if confidence <= 2 else 3 if confidence <= 4 else 7
    return (date.today() + timedelta(days=days)).isoformat()


def checkpoint_path(path: Path) -> Path:
    return path.with_name(path.stem + "_checkpoint.md")


def load_state(path: Path, course: str) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return {"course": course, "topics": {}, "sessions": []}


def write_markdown(state: dict[str, Any], path: Path) -> None:
    lines = [f"# {state.get('course', '课程')} 学习状态", "", "## 知识点", ""]
    lines.extend(["| 知识点 | 状态 | 最近练习 | 下次复习 | 证据 |", "| --- | --- | --- | --- | --- |"])
    for name, info in sorted(state.get("topics", {}).items()):
        evidence = "; ".join(info.get("evidence", [])[-3:])
        lines.append(
            f"| {name} | {info.get('status','unknown')} | {info.get('last_practiced','')} | "
            f"{info.get('next_review','')} | {evidence} |"
        )
    lines.extend(["", "## 最近学习记录", ""])
    for session in state.get("sessions", [])[-10:]:
        lines.append(f"- {session['date']} {session['topic']}：{session['result']}，信心 {session['confidence']}，{session['notes']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checkpoint(state: dict[str, Any], path: Path) -> None:
    topics = state.get("topics", {})
    unfinished = [
        (name, info)
        for name, info in topics.items()
        if info.get("status") != "exam_ready"
    ]
    missed = [s for s in state.get("sessions", []) if s.get("result") == "missed"]
    lines = [
        "# 复习检查点",
        "",
        f"- 课程：{state.get('course', '课程')}",
        f"- 生成日期：{date.today().isoformat()}",
        f"- 最近拖延/未完成次数：{len(missed)}",
        "",
        "## 当前最高优先级",
    ]
    for name, info in unfinished[:5]:
        lines.append(f"- {name}: {info.get('status','unknown')}，下次动作 {info.get('next_action','复测/练习')}")
    lines.extend(["", "## 最近记录"])
    for session in state.get("sessions", [])[-8:]:
        lines.append(f"- {session['date']} {session['topic']}：{session['result']}，信心 {session['confidence']}，{session['notes']}")
    lines.extend(
        [
            "",
            "## 下一步规则",
            "- 如果上一项 missed：立刻降级成 25-45 分钟短任务。",
            "- 先保留 explicit/repeated 的高分内容。",
            "- 如果上下文压缩，先读本检查点和 state.json 再继续。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update study state.")
    parser.add_argument("state", type=Path)
    parser.add_argument("--course", default="未命名课程")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--result", choices=["correct", "partial", "wrong", "missed"], required=True)
    parser.add_argument("--confidence", type=int, default=3)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    state = load_state(args.state, args.course)
    state["course"] = state.get("course") or args.course
    topics = state.setdefault("topics", {})
    info = topics.setdefault(args.topic, {"status": "unknown", "evidence": [], "mistakes": []})
    info["status"] = next_status(info.get("status", "unknown"), args.result, args.confidence)
    info["last_practiced"] = date.today().isoformat()
    info["next_review"] = next_review(args.confidence)
    info.setdefault("evidence", []).append(args.notes or args.result)
    if args.result == "missed":
        info.setdefault("missed_count", 0)
        info["missed_count"] += 1
        info["next_action"] = "降级为 25-45 分钟短任务，优先完成一个可验证产出"
    state.setdefault("sessions", []).append(
        {
            "date": date.today().isoformat(),
            "topic": args.topic,
            "result": args.result,
            "confidence": args.confidence,
            "notes": args.notes,
        }
    )
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(state, args.state.with_suffix(".md"))
    write_checkpoint(state, checkpoint_path(args.state))
    print(f"Updated {args.state}")
    print(f"Wrote {args.state.with_suffix('.md')}")
    print(f"Wrote {checkpoint_path(args.state)}")


if __name__ == "__main__":
    main()
