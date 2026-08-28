#!/usr/bin/env python3
"""Export generated PNGs to stable Godot canvases.

Single-image mode remains backward compatible:
    python scripts/godot_export.py input.png character out --name hero

Asset-group mode computes exactly one union bbox/shared transform for every
paper-doll layer or animation frame in the group:
    python scripts/godot_export.py group character out frame0.png frame1.png frame2.png \
        --group-id hero_walk_down --region loen

Group invariants:
  * source images are padded to one shared source canvas without scaling;
  * alpha cleanup runs before bbox measurement;
  * union bbox, scale, origin, and baseline are computed once;
  * every member uses the same transform and fixed project palette;
  * a JSON transform/provenance sidecar is emitted for regression and registry use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image

from palette_remap import DEFAULT_PALETTE, build_palette, load_palette_config, remap_image


# category: (canvas_w, canvas_h, resize_mode, anchor)
CANVAS = {
    "tile": (32, 32, "stretch", "center"),
    "icon": (32, 32, "fit", "center"),
    "ui": (256, 128, "fit", "center"),
    "character": (32, 48, "fit", "bottom"),
    "layer": (32, 48, "fit", "bottom"),
    "portrait": (64, 64, "fit", "center"),
    "building": (128, 128, "fit", "bottom"),
    "building_l": (256, 256, "fit", "bottom"),
    "plant": (64, 64, "fit", "bottom"),
    "prop": (64, 64, "fit", "center"),
    "vehicle": (160, 128, "fit", "bottom"),
    "vfx": (64, 64, "fit", "center"),
}

WM_X, WM_H = 0.30, 0.10
ALPHA_THRESHOLD = 64
RESAMPLING = {
    "nearest": Image.Resampling.NEAREST,
    "lanczos": Image.Resampling.LANCZOS,
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def erase_watermark(image: Image.Image) -> Image.Image:
    """Clear the known bottom-left generator watermark region."""
    array = np.asarray(image.convert("RGBA")).copy()
    height, width = array.shape[:2]
    array[int(height * (1 - WM_H)) : height, : int(width * WM_X), 3] = 0
    return Image.fromarray(array, "RGBA")


def repair_tile_watermark(image: Image.Image) -> Image.Image:
    """Fill the tile watermark area from a rotated opposite-side patch."""
    array = np.asarray(image.convert("RGBA")).copy()
    height, width = array.shape[:2]
    y0, x1 = int(height * (1 - WM_H)), int(width * WM_X)
    patch_h, patch_w = height - y0, x1
    array[y0:height, 0:x1] = array[0:patch_h, width - patch_w : width][::-1, ::-1]
    return Image.fromarray(array, "RGBA")


def clean_image(
    source: str | Path,
    category: str,
    remove_watermark: bool = True,
    alpha_threshold: int = ALPHA_THRESHOLD,
) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    if remove_watermark:
        image = erase_watermark(image)
        if category == "tile":
            image = repair_tile_watermark(image)
    array = np.asarray(image).copy()
    array[array[..., 3] < alpha_threshold, 3] = 0
    array[..., :3][array[..., 3] == 0] = 0
    return Image.fromarray(array, "RGBA")


def normalize_source_canvases(images: Sequence[Image.Image], anchor: str) -> list[Image.Image]:
    """Pad varying source sizes to one canvas without changing scale."""
    max_width = max(image.width for image in images)
    max_height = max(image.height for image in images)
    normalized: list[Image.Image] = []
    for image in images:
        canvas = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
        x = (max_width - image.width) // 2
        y = (max_height - image.height) // 2 if anchor == "center" else max_height - image.height
        canvas.alpha_composite(image, (x, y))
        normalized.append(canvas)
    return normalized


def union_bbox(images: Sequence[Image.Image]) -> tuple[int, int, int, int]:
    boxes = [image.getchannel("A").getbbox() for image in images]
    boxes = [box for box in boxes if box]
    if not boxes:
        raise ValueError("asset group has no pixels above alpha threshold")
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def compute_shared_transform(
    images: Sequence[Image.Image],
    category: str,
    padding: int = 0,
    baseline: int | None = None,
) -> dict:
    if category not in CANVAS:
        raise ValueError(f"unknown category {category!r}")
    target_width, target_height, mode, anchor = CANVAS[category]
    if mode == "stretch":
        bbox = (0, 0, images[0].width, images[0].height)
        scale_x = target_width / images[0].width
        scale_y = target_height / images[0].height
        return {
            "category": category,
            "canvas": [target_width, target_height],
            "source_canvas": list(images[0].size),
            "union_bbox": list(bbox),
            "scale": [scale_x, scale_y],
            "resized": [target_width, target_height],
            "origin": [0, 0],
            "anchor": anchor,
            "baseline": None,
            "padding": 0,
        }

    bbox = union_bbox(images)
    bbox_width, bbox_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if padding < 0 or padding * 2 >= min(target_width, target_height):
        raise ValueError("padding must leave a non-empty target canvas")
    effective_baseline = target_height - 1 if baseline is None else baseline
    if not 0 <= effective_baseline < target_height:
        raise ValueError(f"baseline must be in [0, {target_height - 1}]")

    available_width = target_width - 2 * padding
    if anchor == "bottom":
        available_height = effective_baseline + 1 - padding
    else:
        available_height = target_height - 2 * padding
    scale = min(available_width / bbox_width, available_height / bbox_height)
    resized_width = max(1, round(bbox_width * scale))
    resized_height = max(1, round(bbox_height * scale))
    origin_x = (target_width - resized_width) // 2
    origin_y = (
        (target_height - resized_height) // 2
        if anchor == "center"
        else effective_baseline - resized_height + 1
    )
    return {
        "category": category,
        "canvas": [target_width, target_height],
        "source_canvas": list(images[0].size),
        "union_bbox": list(bbox),
        "scale": scale,
        "resized": [resized_width, resized_height],
        "origin": [origin_x, origin_y],
        "anchor": anchor,
        "baseline": effective_baseline if anchor == "bottom" else None,
        "padding": padding,
    }


def apply_shared_transform(
    image: Image.Image,
    transform: dict,
    resample: str = "lanczos",
) -> Image.Image:
    cropped = image.crop(tuple(transform["union_bbox"]))
    resized = cropped.resize(tuple(transform["resized"]), RESAMPLING[resample])
    canvas = Image.new("RGBA", tuple(transform["canvas"]), (0, 0, 0, 0))
    canvas.alpha_composite(resized, tuple(transform["origin"]))
    return canvas


def _palette_for_export(
    palette_path: str | Path,
    region: str | None,
    specials: Sequence[str],
) -> tuple[np.ndarray, dict]:
    return build_palette(load_palette_config(palette_path), region=region, specials=specials)


def process_group(
    inputs: Sequence[str | Path],
    category: str,
    out_dir: str | Path,
    names: Sequence[str] | None = None,
    group_id: str | None = None,
    transform_out: str | Path | None = None,
    region: str | None = None,
    specials: Sequence[str] = (),
    palette_path: str | Path = DEFAULT_PALETTE,
    use_palette: bool = True,
    remove_watermark: bool = True,
    alpha_threshold: int = ALPHA_THRESHOLD,
    padding: int = 0,
    baseline: int | None = None,
    resample: str = "lanczos",
) -> tuple[list[str], dict]:
    if not inputs:
        raise ValueError("asset group must contain at least one input")
    if category not in CANVAS:
        raise ValueError(f"unknown category {category!r}")
    _, _, _, anchor = CANVAS[category]
    cleaned = [
        clean_image(path, category, remove_watermark=remove_watermark, alpha_threshold=alpha_threshold)
        for path in inputs
    ]
    normalized = normalize_source_canvases(cleaned, anchor)
    transform = compute_shared_transform(normalized, category, padding=padding, baseline=baseline)
    palette = None
    palette_metadata = {"palette_version": None, "palette_ids": [], "color_count": None}
    if use_palette:
        palette, palette_metadata = _palette_for_export(palette_path, region, specials)

    if names is not None and len(names) != len(inputs):
        raise ValueError("--name count must match the number of input images")
    slugs = list(names) if names is not None else [Path(path).stem for path in inputs]
    destination_dir = Path(out_dir) / category
    destination_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[str] = []
    members = []
    for source, slug, image in zip(inputs, slugs, normalized):
        canvas = apply_shared_transform(image, transform, resample=resample)
        if palette is not None:
            canvas = remap_image(canvas, palette, dither=False)
        destination = destination_dir / f"{slug}.png"
        canvas.save(destination)
        outputs.append(str(destination))
        members.append(
            {
                "source": str(source),
                "source_sha256": sha256_file(source),
                "output": str(destination),
                "slug": slug,
            }
        )

    metadata = {
        "schema_version": 1,
        "group_id": group_id or slugs[0],
        "member_count": len(inputs),
        "alpha_threshold": alpha_threshold,
        "remove_watermark": remove_watermark,
        "resample": resample,
        "region": region,
        "special_palettes": list(specials),
        "palette": palette_metadata,
        "transform": transform,
        "members": members,
    }
    transform_payload = json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode("utf-8")
    metadata["transform_id"] = "transform-" + hashlib.sha256(transform_payload).hexdigest()[:12]
    sidecar = Path(transform_out) if transform_out else destination_dir / f"{metadata['group_id']}.transform.json"
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return outputs, metadata


def process(
    input_path: str | Path,
    category: str,
    out_dir: str | Path,
    name: str | None = None,
    **kwargs,
) -> str:
    outputs, _ = process_group(
        [input_path],
        category,
        out_dir,
        names=[name or Path(input_path).stem],
        group_id=name or Path(input_path).stem,
        **kwargs,
    )
    return outputs[0]


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", default=None, help="region palette id, e.g. loen")
    parser.add_argument("--special", action="append", default=[], help="special palette id; repeatable")
    parser.add_argument("--palette", default=str(DEFAULT_PALETTE))
    parser.add_argument("--no-palette", action="store_true", help="skip palette remap")
    parser.add_argument("--keep-watermark-region", action="store_true")
    parser.add_argument("--alpha-threshold", type=int, default=ALPHA_THRESHOLD)
    parser.add_argument("--padding", type=int, default=0)
    parser.add_argument("--baseline", type=int, default=None)
    parser.add_argument("--resample", choices=sorted(RESAMPLING), default="lanczos")


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "group":
        parser = argparse.ArgumentParser(description="Shared-transform asset-group export")
        parser.add_argument("mode", choices=["group"])
        parser.add_argument("category", choices=sorted(CANVAS))
        parser.add_argument("out_dir")
        parser.add_argument("inputs", nargs="+")
        parser.add_argument("--name", action="append", dest="names")
        parser.add_argument("--group-id", default=None)
        parser.add_argument("--transform-out", default=None)
        _add_common_options(parser)
        args = parser.parse_args(argv)
        outputs, metadata = process_group(
            args.inputs,
            args.category,
            args.out_dir,
            names=args.names,
            group_id=args.group_id,
            transform_out=args.transform_out,
            region=args.region,
            specials=args.special,
            palette_path=args.palette,
            use_palette=not args.no_palette,
            remove_watermark=not args.keep_watermark_region,
            alpha_threshold=args.alpha_threshold,
            padding=args.padding,
            baseline=args.baseline,
            resample=args.resample,
        )
        print(
            f"[{args.category}] {len(outputs)} files; "
            f"shared {metadata['transform_id']} scale={metadata['transform']['scale']}"
        )
        return 0

    parser = argparse.ArgumentParser(description="Generated PNG to Godot-ready pixel asset")
    parser.add_argument("input")
    parser.add_argument("category", choices=sorted(CANVAS))
    parser.add_argument("out_dir")
    parser.add_argument("--name", default=None)
    parser.add_argument("--transform-out", default=None)
    _add_common_options(parser)
    args = parser.parse_args(argv)
    destination = process(
        args.input,
        args.category,
        args.out_dir,
        name=args.name,
        transform_out=args.transform_out,
        region=args.region,
        specials=args.special,
        palette_path=args.palette,
        use_palette=not args.no_palette,
        remove_watermark=not args.keep_watermark_region,
        alpha_threshold=args.alpha_threshold,
        padding=args.padding,
        baseline=args.baseline,
        resample=args.resample,
    )
    print(f"[{args.category}] {destination} ({CANVAS[args.category][0]}x{CANVAS[args.category][1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
