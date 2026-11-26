#!/usr/bin/env python3
"""Read current system time and compute exam countdown context."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


WEEKDAY_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def parse_exam(raw: str, tz: ZoneInfo) -> dict[str, object]:
    if "|" in raw:
        name, value = raw.split("|", 1)
    elif "=" in raw:
        name, value = raw.split("=", 1)
    else:
        name, value = "考试", raw
    value = value.strip().replace("T", " ")
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    parsed = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        raise SystemExit(f"无法解析考试时间：{raw}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return {"course": name.strip(), "exam_at": parsed.isoformat()}


def phase_for(delta: timedelta) -> str:
    seconds = delta.total_seconds()
    if seconds < 0:
        return "已过期"
    hours = seconds / 3600
    if hours <= 3:
        return "考前三小时"
    if hours <= 24:
        return "24小时内"
    if hours <= 48:
        return "48小时内"
    if hours <= 72:
        return "72小时内"
    return "普通复习"


def build_context(args: argparse.Namespace) -> dict[str, object]:
    tz = ZoneInfo(args.timezone)
    now = datetime.now(tz)
    exams = [parse_exam(item, tz) for item in args.exam]
    enriched = []
    for exam in exams:
        exam_at = datetime.fromisoformat(str(exam["exam_at"]))
        delta = exam_at - now
        seconds = int(delta.total_seconds())
        enriched.append(
            {
                **exam,
                "seconds_until": seconds,
                "hours_until": round(seconds / 3600, 2),
                "days_until": round(seconds / 86400, 2),
                "phase": phase_for(delta),
                "status": "past" if seconds < 0 else "future",
            }
        )
    future = sorted((item for item in enriched if item["status"] == "future"), key=lambda item: item["seconds_until"])
    past = sorted((item for item in enriched if item["status"] == "past"), key=lambda item: item["seconds_until"], reverse=True)
    return {
        "now_iso": now.isoformat(),
        "current_date": now.date().isoformat(),
        "current_time": now.strftime("%H:%M:%S"),
        "timezone": args.timezone,
        "weekday": WEEKDAY_ZH[now.weekday()],
        "daypart": daypart(now),
        "exams": enriched,
        "nearest_future_exam": future[0] if future else None,
        "most_recent_past_exam": past[0] if past else None,
    }


def daypart(now: datetime) -> str:
    hour = now.hour
    if 5 <= hour < 12:
        return "上午"
    if 12 <= hour < 14:
        return "中午"
    if 14 <= hour < 18:
        return "下午"
    if 18 <= hour < 23:
        return "晚上"
    return "深夜"


def format_markdown(context: dict[str, object]) -> str:
    lines = [
        "# 当前时间戳",
        "",
        f"- 当前时间：{context['now_iso']}",
        f"- 日期：{context['current_date']}",
        f"- 时间：{context['current_time']}",
        f"- 时区：{context['timezone']}",
        f"- 星期：{context['weekday']}",
        f"- 时段：{context['daypart']}",
    ]
    nearest = context.get("nearest_future_exam")
    if nearest:
        lines.extend(
            [
                "",
                "## 最近未来考试",
                f"- 课程：{nearest['course']}",
                f"- 考试时间：{nearest['exam_at']}",
                f"- 剩余小时：{nearest['hours_until']}",
                f"- 阶段：{nearest['phase']}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Read current system timestamp and exam countdown context.")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--exam", action="append", default=[], help='格式："课程名|YYYY-MM-DD HH:MM"')
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()
    context = build_context(args)
    if args.json:
        print(json.dumps(context, ensure_ascii=True, indent=2))
    else:
        print(format_markdown(context), end="")


if __name__ == "__main__":
    main()
