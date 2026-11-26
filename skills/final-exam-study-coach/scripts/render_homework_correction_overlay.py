#!/usr/bin/env python3
"""Render handwritten-style correction marks onto a homework photo."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


FONT_CANDIDATES = [
    "C:/Windows/Fonts/simkai.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
]


def load_font(size: int) -> ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def dark_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    probe = image.convert("L")
    pixels = probe.load()
    width, height = probe.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            if pixels[x, y] < 115:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def auto_rotate_homework(image: Image.Image) -> Image.Image:
    """Pick a readable rotation for sparse handwritten homework photos."""
    image = ImageOps.exif_transpose(image)
    scale = min(1.0, 700 / max(image.size))
    probe = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
    candidates: list[tuple[float, int]] = []
    for angle in (0, 90, 180, 270):
        rotated = probe.rotate(angle, expand=True)
        bbox = dark_bbox(rotated)
        if bbox is None:
            candidates.append((0.0, angle))
            continue
        x1, y1, x2, y2 = bbox
        ink_w = max(1, x2 - x1)
        ink_h = max(1, y2 - y1)
        center_y = (y1 + y2) / 2 / max(1, rotated.height)
        horizontal_score = ink_w / ink_h
        top_page_bonus = 1.0 - abs(center_y - 0.32)
        candidates.append((horizontal_score * 3 + top_page_bonus, angle))
    angle = max(candidates, key=lambda item: item[0])[1]
    return image.rotate(angle, expand=True)


def orient_image(image: Image.Image, mode: str) -> Image.Image:
    if mode == "none":
        return image
    if mode == "auto":
        return auto_rotate_homework(image)
    angle_by_mode = {
        "ccw90": 90,
        "cw90": 270,
        "180": 180,
    }
    return ImageOps.exif_transpose(image).rotate(angle_by_mode[mode], expand=True)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], fill: str, width: int) -> None:
    draw.line([start, end], fill=fill, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head_len = max(14, width * 4)
    left = (
        end[0] - head_len * math.cos(angle - math.pi / 6),
        end[1] - head_len * math.sin(angle - math.pi / 6),
    )
    right = (
        end[0] - head_len * math.cos(angle + math.pi / 6),
        end[1] - head_len * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, left, right], fill=fill)


def draw_annotation(draw: ImageDraw.ImageDraw, item: dict[str, Any]) -> None:
    color = item.get("color", "#d72638")
    width = int(item.get("width", 4))
    kind = item.get("type")
    if kind == "circle":
        x, y, w, h = [float(item.get(k, 0)) for k in ("x", "y", "w", "h")]
        for offset in range(width):
            draw.ellipse([x - offset, y - offset, x + w + offset, y + h + offset], outline=color)
    elif kind == "box":
        x, y, w, h = [float(item.get(k, 0)) for k in ("x", "y", "w", "h")]
        for offset in range(width):
            draw.rounded_rectangle([x - offset, y - offset, x + w + offset, y + h + offset], radius=10, outline=color)
    elif kind == "arrow":
        start = (float(item.get("x", 0)), float(item.get("y", 0)))
        end = (float(item.get("x2", 0)), float(item.get("y2", 0)))
        arrow(draw, start, end, color, width)
    elif kind == "text":
        x, y = float(item.get("x", 0)), float(item.get("y", 0))
        font = load_font(int(item.get("font_size", 30)))
        text = str(item.get("text", ""))
        draw.multiline_text((x, y), text, font=font, fill=color, spacing=6)
    elif kind == "check":
        x, y = float(item.get("x", 0)), float(item.get("y", 0))
        draw.line([(x, y + 14), (x + 14, y + 30), (x + 42, y)], fill=color, width=width)
    elif kind == "cross":
        x, y = float(item.get("x", 0)), float(item.get("y", 0))
        draw.line([(x, y), (x + 36, y + 36)], fill=color, width=width)
        draw.line([(x + 36, y), (x, y + 36)], fill=color, width=width)


def write_review(path: Path, data: dict[str, Any]) -> None:
    lines = [f"# {data.get('title', '浣滀笟鎵规敼璇存槑')}", ""]
    for idx, item in enumerate(data.get("annotations", []), 1):
        explanation = item.get("explanation")
        if explanation:
            lines.append(f"{idx}. {explanation}")
    if len(lines) == 2:
        lines.append("暂无文字解释。")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw correction marks onto a homework image.")
    parser.add_argument("image", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path)
    parser.add_argument(
        "--orientation",
        choices=("auto", "none", "ccw90", "cw90", "180"),
        default="auto",
        help="Normalize homework photo orientation before drawing annotations. Coordinates apply after orientation.",
    )
    args = parser.parse_args()

    data = json.loads(args.annotations.read_text(encoding="utf-8-sig"))
    image = orient_image(Image.open(args.image).convert("RGB"), args.orientation)
    draw = ImageDraw.Draw(image)
    for item in data.get("annotations", []):
        draw_annotation(draw, item)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    if args.review_output:
        write_review(args.review_output, data)
    print(f"wrote {args.output}")
    if args.review_output:
        print(f"wrote {args.review_output}")


if __name__ == "__main__":
    main()
