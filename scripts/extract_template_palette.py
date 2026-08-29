#!/usr/bin/env python3
"""Derive the frozen Tingen palette from authoritative Loen template scenes.

Every registered RGB is an exact pixel observed in a HUD-free crop of the
source templates. The extractor reduces hundreds of thousands of generated
near-colors into stable HSV strata, then chooses source-color medoids. Runtime
tools consume the committed JSON; they never sample Scene Bible images.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


SCHEMA_VERSION = 1
DERIVATION_VERSION = "tingen-template-medoids-v1"
CROP_NORM = (0.25, 0.0, 0.835, 0.80)
SAMPLE_SIZE = (384, 296)
GROUP_SLOTS = {
    "outline": 8,
    "neutral_dark": 8,
    "neutral_light": 10,
    "red_masonry": 8,
    "gold_wood": 10,
    "foliage": 10,
    "blue_slate_glass": 8,
    "purple_accent": 2,
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rgb_hex(color: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02X}" for channel in color)


def _hud_free_crop(image: Image.Image) -> Image.Image:
    width, height = image.size
    crop = (
        round(width * CROP_NORM[0]),
        round(height * CROP_NORM[1]),
        round(width * CROP_NORM[2]),
        round(height * CROP_NORM[3]),
    )
    return image.convert("RGB").crop(crop)


def _classify(rgb: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    height = max(1, math.ceil(len(rgb) / 1024))
    padded = np.empty((height * 1024, 3), dtype=np.uint8)
    padded[: len(rgb)] = rgb
    padded[len(rgb) :] = rgb[-1]
    hsv = np.asarray(Image.fromarray(padded.reshape(height, 1024, 3), "RGB").convert("HSV")).reshape(-1, 3)
    hsv = hsv[: len(rgb)]
    hue, saturation, value = hsv[:, 0], hsv[:, 1], hsv[:, 2]
    masks: dict[str, np.ndarray] = {}
    remaining = np.ones(len(rgb), dtype=bool)

    masks["outline"] = value < 50
    remaining &= ~masks["outline"]
    masks["neutral_dark"] = remaining & (saturation < 45) & (value < 135)
    remaining &= ~masks["neutral_dark"]
    masks["neutral_light"] = remaining & (saturation < 45)
    remaining &= ~masks["neutral_light"]
    masks["red_masonry"] = remaining & ((hue < 18) | (hue >= 245))
    remaining &= ~masks["red_masonry"]
    masks["gold_wood"] = remaining & (hue < 50)
    remaining &= ~masks["gold_wood"]
    masks["foliage"] = remaining & (hue < 125)
    remaining &= ~masks["foliage"]
    masks["blue_slate_glass"] = remaining & (hue < 190)
    remaining &= ~masks["blue_slate_glass"]
    masks["purple_accent"] = remaining
    return hsv, masks


def _source_medoids(pixels: np.ndarray, count: int) -> list[tuple[int, int, int]]:
    unique, frequencies = np.unique(pixels, axis=0, return_counts=True)
    count = min(count, len(unique))
    if count == 0:
        return []
    width = min(1024, len(pixels))
    height = math.ceil(len(pixels) / width)
    canvas = np.empty((height * width, 3), dtype=np.uint8)
    canvas[: len(pixels)] = pixels
    canvas[len(pixels) :] = pixels[-1]
    quantized = Image.fromarray(canvas.reshape(height, width, 3), "RGB").quantize(
        colors=count,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    used = sorted(color_index for _, color_index in quantized.getcolors(maxcolors=256) or [])
    raw_palette = quantized.getpalette() or []
    centroids = [np.asarray(raw_palette[index * 3 : index * 3 + 3], dtype=np.int32) for index in used]
    candidates = unique.astype(np.int32)
    chosen_indices: set[int] = set()
    selected: list[tuple[int, int, int]] = []
    for centroid in centroids:
        distance = ((candidates - centroid) ** 2).sum(axis=1).astype(np.int64)
        if chosen_indices:
            distance[list(chosen_indices)] = np.iinfo(np.int64).max
        minimum = distance.min()
        nearest = np.flatnonzero(distance == minimum)
        chosen = int(nearest[np.argmax(frequencies[nearest])])
        chosen_indices.add(chosen)
        selected.append(tuple(int(channel) for channel in unique[chosen]))
    selected.sort(key=lambda color: (sum(color), color))
    return selected


def _hsv_of(color: tuple[int, int, int]) -> tuple[int, int, int]:
    image = Image.new("RGB", (1, 1), color)
    return tuple(int(value) for value in image.convert("HSV").getpixel((0, 0)))


def _tone_ramp(colors: list[tuple[int, int, int]]) -> list[dict[str, str]]:
    """Choose semantic tone roles without inventing colors between source pixels."""
    ordered = sorted(dict.fromkeys(colors), key=lambda color: (_hsv_of(color)[2], sum(color), color))
    role_sets = {
        1: ("midtone",),
        2: ("shadow", "highlight"),
        3: ("shadow", "midtone", "highlight"),
        4: ("deep_shadow", "shadow", "midtone", "highlight"),
        5: ("deep_shadow", "shadow", "midtone", "light", "highlight"),
    }
    count = min(5, len(ordered))
    if not count:
        return []
    if len(ordered) == count:
        selected = ordered
    else:
        indices = [round(index * (len(ordered) - 1) / (count - 1)) for index in range(count)]
        selected = [ordered[index] for index in indices]
    return [
        {"role": role, "color": rgb_hex(color)}
        for role, color in zip(role_sets[count], selected)
    ]


def build_material_registry(groups: dict[str, list[tuple[int, int, int]]], palette_version: str) -> dict:
    all_colors = [color for group in groups.values() for color in group]
    outline = groups["outline"]
    neutral_dark = groups["neutral_dark"]
    neutral_light = groups["neutral_light"]
    red = groups["red_masonry"]
    gold = groups["gold_wood"]
    green = groups["foliage"]
    blue = groups["blue_slate_glass"]

    dark = lambda color: _hsv_of(color)[2] < 145
    light = lambda color: _hsv_of(color)[2] >= 135
    low_sat = lambda color: _hsv_of(color)[1] < 105
    high_sat = lambda color: _hsv_of(color)[1] >= 70
    materials = {
        "outline.shared": outline + neutral_dark[:2],
        "stone.warm_dressed": [color for color in neutral_light + gold + red if light(color) and low_sat(color)],
        "stone.cool_slate": neutral_dark + neutral_light + [color for color in blue if low_sat(color)],
        "wood.warm": [color for color in gold + red if dark(color) or _hsv_of(color)[2] < 220],
        "door.dark_green_civic": [color for color in green if dark(color)],
        "glass.slate_blue": [color for color in blue + neutral_light if _hsv_of(color)[2] >= 75],
        "iron.black_cast": outline + [color for color in neutral_dark if dark(color)],
        "terrain.cobblestone": neutral_dark + neutral_light + [color for color in gold if low_sat(color)],
        "terrain.grass": green,
        "skin.fair": [color for color in gold + red if light(color) and low_sat(color)],
        "cloth.navy": [color for color in blue if dark(color)] + outline[:2],
        "metal.warm_brass": [color for color in gold if high_sat(color) and _hsv_of(color)[2] >= 90],
    }
    fallback_by_material = {
        "stone.warm_dressed": neutral_light,
        "stone.cool_slate": neutral_dark + neutral_light + blue,
        "wood.warm": gold + red,
        "door.dark_green_civic": green,
        "glass.slate_blue": blue + neutral_light,
        "iron.black_cast": outline + neutral_dark,
        "terrain.cobblestone": neutral_dark + neutral_light,
        "terrain.grass": green,
        "skin.fair": gold + red + neutral_light,
        "cloth.navy": blue + outline,
        "metal.warm_brass": gold,
        "outline.shared": outline + neutral_dark,
    }
    output = {}
    for material_id, selected in materials.items():
        selected = list(dict.fromkeys(selected))
        if len(selected) < 3:
            selected.extend(color for color in fallback_by_material[material_id] if color not in selected)
        ordered = sorted(selected, key=lambda color: (_hsv_of(color)[2], sum(color), color))
        ramp = _tone_ramp(ordered)
        output[material_id] = {
            "colors": [rgb_hex(color) for color in ordered],
            "tone_ramp": ramp,
            "minimum_tone_roles": 0 if material_id == "outline.shared" else min(3, len(ramp)),
            "audit_tone_usage": material_id != "outline.shared",
            "shading_policy": "clustered_pixel_shading_no_smooth_gradient",
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "palette_version": palette_version,
        "approval_status": "approved_from_template_pack",
        "source_authority": "user-designated Loen/Tingen template scenes",
        "composite_remap_policy": "material_masks_required_no_global_nearest_color",
        "flat_fill_policy": "review_when_declared_material_uses_fewer_than_minimum_tone_roles",
        "common_material_ids": ["outline.shared"],
        "materials": output,
        "registered_palette_color_count": len(set(all_colors)),
    }


def derive_palette(source_zip: str | Path, member_prefix: str = "场景包/鲁恩王国/") -> tuple[dict, dict, list[tuple[int, int, int]]]:
    source_zip = Path(source_zip)
    member_records = []
    samples = []
    with zipfile.ZipFile(source_zip) as archive:
        entries = sorted(
            (entry for entry in archive.infolist() if entry.filename.startswith(member_prefix) and entry.filename.endswith(".png")),
            key=lambda entry: entry.filename,
        )
        if len(entries) != 10:
            raise ValueError(f"expected 10 authoritative template PNGs under {member_prefix!r}; found {len(entries)}")
        for entry in entries:
            payload = archive.read(entry)
            image = Image.open(io.BytesIO(payload)).convert("RGB")
            crop = _hud_free_crop(image)
            sample = crop.resize(SAMPLE_SIZE, Image.Resampling.NEAREST)
            samples.append(np.asarray(sample).reshape(-1, 3))
            member_records.append(
                {
                    "member": entry.filename,
                    "sha256": sha256_bytes(payload),
                    "source_size": list(image.size),
                    "crop_norm": list(CROP_NORM),
                    "sample_size": list(SAMPLE_SIZE),
                }
            )
    rgb = np.concatenate(samples, axis=0).astype(np.uint8)
    _, masks = _classify(rgb)
    groups = {
        group: _source_medoids(rgb[mask], GROUP_SLOTS[group])
        for group, mask in masks.items()
    }
    palette = list(dict.fromkeys(color for group in GROUP_SLOTS for color in groups[group]))
    if len(palette) < sum(GROUP_SLOTS.values()):
        unique, counts = np.unique(rgb, axis=0, return_counts=True)
        for index in np.argsort(counts)[::-1]:
            color = tuple(int(channel) for channel in unique[index])
            if color not in palette:
                palette.append(color)
            if len(palette) == sum(GROUP_SLOTS.values()):
                break
    palette = palette[: sum(GROUP_SLOTS.values())]
    palette_version = "tingen_pixel_v3_hd"
    palette_json = {
        "schema_version": SCHEMA_VERSION,
        "palette_version": palette_version,
        "approval_status": "approved_from_template_pack",
        "master": {
            "id": "tingen-template-master-v1",
            "description": "Frozen 64-color source-medoid palette derived from ten user-approved Loen/Tingen templates.",
            "colors": [rgb_hex(color) for color in palette],
        },
        "regions": {"loen": {"id": "tingen-template-loen-v1", "colors": []}},
        "special": {},
        "groups": {group: [rgb_hex(color) for color in colors] for group, colors in groups.items()},
        "derivation": {
            "algorithm": DERIVATION_VERSION,
            "rule": "Every registered RGB is an exact observed source pixel; generated centroids are never registered.",
            "source_archive": source_zip.name,
            "source_archive_sha256": sha256_file(source_zip),
            "member_prefix": member_prefix,
            "members": member_records,
            "group_slots": GROUP_SLOTS,
            "hud_exclusion": "central crop before sampling",
            "runtime_sampling": False,
        },
    }
    materials_json = build_material_registry(groups, palette_version)
    materials_json["derivation_algorithm"] = DERIVATION_VERSION
    materials_json["source_palette_id"] = palette_json["master"]["id"]
    return palette_json, materials_json, palette


def render_preview(colors: list[tuple[int, int, int]], destination: str | Path) -> None:
    columns, cell = 8, 32
    rows = math.ceil(len(colors) / columns)
    image = Image.new("RGB", (columns * cell, rows * cell), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    for index, color in enumerate(colors):
        x = (index % columns) * cell
        y = (index // columns) * cell
        draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=color)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze the Tingen palette from authoritative template scenes")
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("--palette-out", type=Path, default=Path("assets/palettes/tingen-template-palette.json"))
    parser.add_argument("--materials-out", type=Path, default=Path("assets/palettes/tingen-materials.json"))
    parser.add_argument("--preview-out", type=Path, default=Path("assets/palettes/tingen-template-palette.png"))
    parser.add_argument("--member-prefix", default="场景包/鲁恩王国/")
    args = parser.parse_args()
    palette, materials, colors = derive_palette(args.source_zip, args.member_prefix)
    for destination, payload in ((args.palette_out, palette), (args.materials_out, materials)):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    render_preview(colors, args.preview_out)
    print(json.dumps({"palette": str(args.palette_out), "materials": str(args.materials_out), "preview": str(args.preview_out), "colors": len(colors)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
