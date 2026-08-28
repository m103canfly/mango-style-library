#!/usr/bin/env python3
"""Audit asset dominant colors against the fixed project palette hierarchy.

Scene images are intentionally not accepted as dynamic palette sources. Select a
Master Palette plus explicit Region/Special extensions so repeated audits are
comparable across time and machines.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from palette_remap import DEFAULT_PALETTE, build_palette, load_palette_config


def palette_of(pixels: np.ndarray, count: int) -> np.ndarray:
    pixels = pixels.astype(np.uint32)
    bins = (pixels[:, 0] >> 3) << 10 | (pixels[:, 1] >> 3) << 5 | (pixels[:, 2] >> 3)
    values, frequencies = np.unique(bins, return_counts=True)
    top = values[frequencies.argsort()[::-1][:count]]
    return np.asarray(
        [
            (((value >> 10) & 31) * 8 + 4, ((value >> 5) & 31) * 8 + 4, (value & 31) * 8 + 4)
            for value in top
        ]
    )


def asset_dominant(path: str | Path, count: int = 5) -> np.ndarray | None:
    array = np.asarray(Image.open(path).convert("RGBA"))
    pixels = array[array[..., 3] > 100][:, :3]
    return palette_of(pixels, count) if len(pixels) else None


def audit(assets_dir: str | Path, benchmark: np.ndarray, tolerance: int) -> list[dict]:
    output = []
    for root, _, files in os.walk(assets_dir):
        for filename in sorted(files):
            if not filename.lower().endswith(".png"):
                continue
            path = Path(root) / filename
            dominant = asset_dominant(path)
            if dominant is None:
                continue
            colors = []
            for color in dominant:
                distance = float(
                    np.sqrt(((benchmark.astype(np.int32) - color.astype(np.int32)) ** 2).sum(axis=1)).min()
                )
                colors.append({"rgb": [int(value) for value in color], "distance": round(distance)})
            outliers = sum(item["distance"] > tolerance for item in colors)
            verdict = "PASS" if outliers == 0 else ("REVIEW" if outliers == 1 else "FLAG")
            output.append(
                {
                    "path": path.as_posix(),
                    "dominant": colors,
                    "worst_distance": max(item["distance"] for item in colors),
                    "verdict": verdict,
                }
            )
    order = {"FLAG": 0, "REVIEW": 1, "PASS": 2}
    output.sort(key=lambda item: (order[item["verdict"]], item["path"]))
    return output


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def render_sheet(rows: list[dict], benchmark: np.ndarray, tolerance: int, destination: str | Path) -> None:
    row_height, thumb, width = 64, 56, 900
    sheet = Image.new("RGB", (width, 100 + len(rows) * row_height + 20), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)
    draw.text((width // 2, 12), "素材库固定调色板审查", font=_font(26, True), fill=(40, 35, 30), anchor="ma")
    for index, color in enumerate(benchmark[:18]):
        x = 30 + index * 46
        draw.rectangle([x, 48, x + 40, 78], fill=tuple(int(value) for value in color), outline=(90, 90, 90))
    verdict_colors = {"PASS": (46, 130, 60), "REVIEW": (200, 140, 20), "FLAG": (200, 50, 40)}
    for index, row in enumerate(rows):
        y = 100 + index * row_height
        image = Image.open(row["path"]).convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        crop = image.crop(bbox) if bbox else image
        scale = min((thumb - 6) / crop.width, (thumb - 6) / crop.height)
        display = crop.resize(
            (max(1, int(crop.width * scale)), max(1, int(crop.height * scale))), Image.Resampling.NEAREST
        )
        checker = Image.new("RGB", (thumb, thumb), (190, 190, 190))
        checker.paste(display, ((thumb - display.width) // 2, (thumb - display.height) // 2), display)
        sheet.paste(checker, (10, y + 4))
        draw.text((74, y + 8), "/".join(Path(row["path"]).parts[-2:]), font=_font(13), fill=(40, 35, 30))
        draw.text((74, y + 30), f"最差距离 {row['worst_distance']}", font=_font(13), fill=(110, 105, 95))
        for color_index, color in enumerate(row["dominant"]):
            x = 300 + color_index * 110
            draw.rectangle([x, y + 10, x + 40, y + 40], fill=tuple(color["rgb"]), outline=(90, 90, 90))
            draw.text(
                (x + 48, y + 18),
                f"Δ{color['distance']}",
                font=_font(13),
                fill=(200, 50, 40) if color["distance"] > tolerance else (110, 105, 95),
            )
        verdict = row["verdict"]
        draw.rectangle([width - 90, y + 14, width - 14, y + 42], outline=verdict_colors[verdict], width=2)
        draw.text((width - 52, y + 20), verdict, font=_font(18, True), fill=verdict_colors[verdict], anchor="ma")
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit assets against fixed Mango palettes")
    parser.add_argument("assets_dir")
    parser.add_argument("--palette", default=str(DEFAULT_PALETTE))
    parser.add_argument("--region", default=None)
    parser.add_argument("--special", action="append", default=[])
    parser.add_argument("--tol", type=int, default=24)
    parser.add_argument("--sheet", default=None)
    parser.add_argument("--json", dest="json_path", default=None)
    args = parser.parse_args()
    benchmark, palette_metadata = build_palette(
        load_palette_config(args.palette), region=args.region, specials=args.special
    )
    rows = audit(args.assets_dir, benchmark, args.tol)
    totals = {verdict: sum(row["verdict"] == verdict for row in rows) for verdict in ("PASS", "REVIEW", "FLAG")}
    result = {
        "schema_version": 1,
        "palette": palette_metadata,
        "region": args.region,
        "special": args.special,
        "tolerance": args.tol,
        "totals": totals,
        "assets": rows,
    }
    for row in rows:
        print(f"{row['verdict']:6s} Δ{row['worst_distance']:3d}  {row['path']}")
    print(json.dumps({"totals": totals, "palette": palette_metadata}, ensure_ascii=False))
    if args.sheet:
        render_sheet(rows, benchmark, args.tol, args.sheet)
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
