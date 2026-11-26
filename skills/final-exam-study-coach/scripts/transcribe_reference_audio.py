#!/usr/bin/env python3
"""Transcribe a reference audio file while preserving segment timestamps."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe reference audio for structure and pacing analysis."
    )
    parser.add_argument("input", type=Path, help="Input WAV or other audio file")
    parser.add_argument("--output", required=True, type=Path, help="UTF-8 Markdown output")
    parser.add_argument("--model", default="small", help="faster-whisper model name")
    parser.add_argument("--language", default="zh", help="Language code; default: zh")
    parser.add_argument("--device", default="cpu", help="Inference device")
    parser.add_argument("--compute-type", default="int8", help="Inference precision")
    return parser.parse_args()


def format_time(seconds: float) -> str:
    total_ms = max(0, round(seconds * 1000))
    minutes, remainder = divmod(total_ms, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    target = args.output.expanduser().resolve()

    if not source.is_file():
        print(f"Input file not found: {source}", file=sys.stderr)
        return 2

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print(
            "faster-whisper is not installed. Run: python -m pip install faster-whisper",
            file=sys.stderr,
        )
        return 2

    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
    )
    segments, info = model.transcribe(
        str(source),
        language=args.language,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
    )

    captured = []
    transcript_parts = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        captured.append(
            f"- [{format_time(segment.start)} - {format_time(segment.end)}] {text}"
        )
        transcript_parts.append(text)

    target.parent.mkdir(parents=True, exist_ok=True)
    output = [
        "# 声音样本转写",
        "",
        f"- 检测语言：`{info.language}`",
        f"- 语言置信度：`{info.language_probability:.3f}`",
        f"- 模型：`{args.model}`",
        "",
        "## 分段转写",
        "",
        *captured,
        "",
        "## 连续文本",
        "",
        "".join(transcript_parts),
        "",
    ]
    target.write_text("\n".join(output), encoding="utf-8")
    print(f"Transcript written: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
