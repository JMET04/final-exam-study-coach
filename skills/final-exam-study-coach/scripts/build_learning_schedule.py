#!/usr/bin/env python3
"""Build a personalized learning schedule table with procrastination buffer."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path


PACE_FACTOR = {"fast": 0.8, "normal": 1.0, "slow": 1.35}


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_topics(raw: str) -> list[tuple[str, int]]:
    topics: list[tuple[str, int]] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            name, minutes = item.rsplit(":", 1)
            topics.append((name.strip(), int(minutes.strip())))
        else:
            topics.append((item, 45))
    return topics


def load_topics(args: argparse.Namespace) -> list[tuple[str, int]]:
    if args.topics_file:
        payload = json.loads(args.topics_file.read_text(encoding="utf-8"))
        return [(str(item["name"]), int(item.get("minutes", 45))) for item in payload.get("topics", [])]
    return parse_topics(args.topics)


def review_label(day: date) -> str:
    return f"当天口述；{day + timedelta(days=1)} 复测；{day + timedelta(days=3)} 变式"


def build_rows(args: argparse.Namespace) -> list[dict[str, str | int]]:
    topics = load_topics(args)
    factor = PACE_FACTOR[args.pace]
    day = parse_date(args.start)
    deadline = parse_date(args.deadline)
    total_days = (deadline - day).days + 1
    core_days = args.core_days or max(1, int(total_days * 0.75))
    core_deadline = min(deadline, day + timedelta(days=core_days - 1))

    rows: list[dict[str, str | int]] = []
    used_today = 0
    for topic, base_minutes in topics:
        minutes = max(20, int(round(base_minutes * factor / 5) * 5))
        if used_today + minutes > args.daily_minutes and used_today > 0:
            day += timedelta(days=1)
            used_today = 0
        if day > core_deadline:
            rows.append(
                {
                    "date": str(day),
                    "block": "缓冲补救",
                    "minutes": min(30, args.daily_minutes),
                    "task": f"核心期已满，先处理 {topic} 的最小得分版本。",
                    "output": "一张规则卡 + 1道典型题",
                    "review": review_label(day),
                    "fallback": "若仍没完成，只背公式/步骤并做一道最典型题。",
                }
            )
            continue
        rows.append(
            {
                "date": str(day),
                "block": topic,
                "minutes": minutes,
                "task": f"学习 {topic}：讲解、主动回忆、做题或模板输出。",
                "output": "理解卡/错题规则/限时题至少一种。",
                "review": review_label(day),
                "fallback": "压缩为15分钟口述 + 1道最典型题。",
            }
        )
        used_today += minutes

    buffer_day = core_deadline + timedelta(days=1)
    while buffer_day <= deadline:
        rows.append(
            {
                "date": str(buffer_day),
                "block": "缓冲与复盘",
                "minutes": min(args.daily_minutes, 90),
                "task": "如果前面拖延，用本块补高证据高分内容；如果已完成，做错题回炉和混合测。",
                "output": "错题清单 + 复测分数 + 考前规则卡",
                "review": "考前回炉",
                "fallback": "只保留最高频错因和最可能得分题型。",
            }
        )
        buffer_day += timedelta(days=1)
    return rows


def write_markdown(rows: list[dict[str, str | int]], args: argparse.Namespace) -> str:
    lines = [
        f"# {args.course} 个性化学习计划表",
        "",
        f"- 起止：{args.start} 至 {args.deadline}",
        f"- 每日可用：{args.daily_minutes} 分钟",
        f"- 学习速度：{args.pace}",
        "- 缓冲规则：核心任务按约70-80%时间完成，剩余时间用于拖延补救、错题回炉和模拟。",
        "",
        "| 日期 | 学习块 | 预计分钟 | 任务 | 产出 | 复习点 | 如果没完成 |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['date']} | {row['block']} | {row['minutes']} | {row['task']} | {row['output']} | {row['review']} | {row['fallback']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a personalized study schedule table.")
    parser.add_argument("--course", required=True)
    parser.add_argument("--topics", default="")
    parser.add_argument("--topics-file", type=Path)
    parser.add_argument("--start", required=True)
    parser.add_argument("--deadline", required=True)
    parser.add_argument("--daily-minutes", type=int, required=True)
    parser.add_argument("--pace", choices=sorted(PACE_FACTOR), default="normal")
    parser.add_argument("--core-days", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.topics and not args.topics_file:
        parser.error("one of --topics or --topics-file is required")
    rows = build_rows(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(write_markdown(rows, args), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
