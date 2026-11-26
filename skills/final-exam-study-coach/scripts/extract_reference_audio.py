#!/usr/bin/env python3
"""Extract only the audio track from a reference video for style analysis."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


SUPPORTED_INPUTS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".m4v",
    ".mp3",
    ".m4a",
    ".wav",
    ".aac",
    ".flac",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a 16 kHz mono WAV without reading or analyzing video frames."
    )
    parser.add_argument("input", type=Path, help="Reference video or audio file")
    parser.add_argument("--output", required=True, type=Path, help="Output WAV path")
    parser.add_argument(
        "--ffmpeg",
        type=Path,
        help="Optional explicit ffmpeg executable path",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file",
    )
    return parser.parse_args()


def resolve_ffmpeg(explicit_path: Path | None) -> str:
    if explicit_path is not None:
        candidate = explicit_path.expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"ffmpeg not found: {candidate}")
        return str(candidate)

    discovered = shutil.which("ffmpeg")
    if discovered is None:
        raise FileNotFoundError(
            "ffmpeg is not available. Install it or pass --ffmpeg with its full path."
        )
    return discovered


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    target = args.output.expanduser().resolve()

    if not source.is_file():
        print(f"Input file not found: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() not in SUPPORTED_INPUTS:
        print(f"Unsupported input format: {source.suffix}", file=sys.stderr)
        return 2
    if target.suffix.lower() != ".wav":
        print("Output must use the .wav extension.", file=sys.stderr)
        return 2
    if target.exists() and not args.overwrite:
        print(
            f"Output already exists: {target}. Use --overwrite to replace it.",
            file=sys.stderr,
        )
        return 2

    try:
        ffmpeg = resolve_ffmpeg(args.ffmpeg)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    target.parent.mkdir(parents=True, exist_ok=True)
    overwrite_flag = "-y" if args.overwrite else "-n"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        overwrite_flag,
        "-i",
        str(source),
        "-vn",
        "-map",
        "0:a:0",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(target),
    ]

    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        if target.exists():
            target.unlink()
        print(
            "Audio extraction failed. Confirm that the source contains an audio track.",
            file=sys.stderr,
        )
        return completed.returncode

    print(f"Extracted audio only: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
