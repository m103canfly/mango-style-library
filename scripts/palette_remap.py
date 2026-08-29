#!/usr/bin/env python3
"""Remap RGBA artwork to the project's shared palette hierarchy.

The output palette is deterministic: Master Palette plus an optional Region Accent
Palette and one or more Special Palettes. Alpha is hardened to 0/255 and
transparent pixels are never allowed to influence color selection. This is a
candidate/reference helper; native Tingen 1x delivery is validated against
declared material sub-palettes and is not globally nearest-color quantized.

Examples:
    python scripts/palette_remap.py input.png output.png
    python scripts/palette_remap.py input.png output.png --region loen
    python scripts/palette_remap.py input.png output.png --special vfx --dither
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from PIL import Image


DEFAULT_PALETTE = Path(__file__).resolve().parents[1] / "assets" / "palettes" / "palettes.json"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"invalid RGB hex color: {value!r}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def load_palette_config(path: str | Path = DEFAULT_PALETTE) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_palette(
    config: dict,
    region: str | None = None,
    specials: Sequence[str] = (),
) -> tuple[np.ndarray, dict]:
    colors: list[tuple[int, int, int]] = []
    palette_ids = [config["master"]["id"]]
    colors.extend(_hex_to_rgb(value) for value in config["master"]["colors"])

    if region:
        try:
            region_palette = config["regions"][region]
        except KeyError as exc:
            choices = ", ".join(sorted(config.get("regions", {})))
            raise ValueError(f"unknown region {region!r}; choose from: {choices}") from exc
        colors.extend(_hex_to_rgb(value) for value in region_palette["colors"])
        palette_ids.append(region_palette["id"])

    for special in specials:
        try:
            special_palette = config["special"][special]
        except KeyError as exc:
            choices = ", ".join(sorted(config.get("special", {})))
            raise ValueError(f"unknown special palette {special!r}; choose from: {choices}") from exc
        colors.extend(_hex_to_rgb(value) for value in special_palette["colors"])
        palette_ids.append(special_palette["id"])

    deduped = list(dict.fromkeys(colors))
    if len(deduped) > 256:
        raise ValueError(f"combined palette has {len(deduped)} colors; PNG indexed limit is 256")
    return np.asarray(deduped, dtype=np.uint8), {
        "palette_version": config["palette_version"],
        "palette_ids": palette_ids,
        "color_count": len(deduped),
    }


def _nearest_palette(rgb: np.ndarray, palette: np.ndarray, chunk_size: int = 65536) -> np.ndarray:
    flat = rgb.reshape(-1, 3).astype(np.int32)
    out = np.empty_like(flat, dtype=np.uint8)
    pal = palette.astype(np.int32)
    for start in range(0, len(flat), chunk_size):
        chunk = flat[start : start + chunk_size]
        distance = ((chunk[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        out[start : start + chunk_size] = palette[distance.argmin(axis=1)]
    return out.reshape(rgb.shape)


def _pillow_palette(palette: np.ndarray) -> Image.Image:
    palette_image = Image.new("P", (1, 1))
    flat = palette.reshape(-1).tolist()
    flat.extend([0] * (768 - len(flat)))
    palette_image.putpalette(flat)
    return palette_image


def remap_image(image: Image.Image, palette: np.ndarray, dither: bool = False) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha_array = np.asarray(rgba.getchannel("A"))
    hard_alpha = Image.fromarray(np.where(alpha_array >= 128, 255, 0).astype(np.uint8), "L")
    if dither:
        rgb = rgba.convert("RGB").quantize(
            palette=_pillow_palette(palette),
            dither=Image.Dither.FLOYDSTEINBERG,
        ).convert("RGB")
        out = rgb.convert("RGBA")
        out.putalpha(hard_alpha)
        return out

    array = np.asarray(rgba).copy()
    array[..., 3] = np.asarray(hard_alpha)
    opaque = array[..., 3] == 255
    if opaque.any():
        array[..., :3][opaque] = _nearest_palette(array[..., :3][opaque], palette)
    array[..., :3][~opaque] = 0
    return Image.fromarray(array, "RGBA")


def remap_path(
    source: str | Path,
    destination: str | Path,
    palette_path: str | Path = DEFAULT_PALETTE,
    region: str | None = None,
    specials: Iterable[str] = (),
    dither: bool = False,
) -> dict:
    config = load_palette_config(palette_path)
    palette, metadata = build_palette(config, region, tuple(specials))
    output = remap_image(Image.open(source), palette, dither=dither)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    output.save(destination)
    metadata.update({"source": str(source), "destination": str(destination), "region": region})
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Remap PNG colors to the shared Mango palette")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--palette", default=str(DEFAULT_PALETTE))
    parser.add_argument("--region", default=None)
    parser.add_argument("--special", action="append", default=[])
    parser.add_argument("--dither", action="store_true")
    parser.add_argument("--metadata", default=None, help="optional JSON provenance output")
    args = parser.parse_args()
    metadata = remap_path(
        args.input,
        args.output,
        palette_path=args.palette,
        region=args.region,
        specials=args.special,
        dither=args.dither,
    )
    if args.metadata:
        Path(args.metadata).write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
