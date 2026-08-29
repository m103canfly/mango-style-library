#!/usr/bin/env python3
"""Machine-readable Tingen project contract helpers.

This module validates native 1x pixel-authored PNGs. It intentionally does not
turn generated HD references into runtime assets.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "profiles" / "tingen_pixel_v3_hd" / "profile.json"
APPROVED_PALETTE_STATUSES = frozenset({"approved", "approved_from_template_pack"})


def palette_is_approved(status: object) -> bool:
    return status in APPROVED_PALETTE_STATUSES


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def resolve_project_path(profile_path: str | Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    profile_path = Path(profile_path).resolve()
    for parent in (ROOT, *profile_path.parents):
        resolved = parent / candidate
        if resolved.exists():
            return resolved
    return ROOT / candidate


def material_colors(
    profile: dict,
    profile_path: str | Path,
    material_ids: Iterable[str],
) -> tuple[set[tuple[int, int, int]], dict]:
    registry_path = resolve_project_path(profile_path, profile["palette"]["material_registry"])
    registry = load_json(registry_path)
    materials = registry["materials"]
    selected = list(dict.fromkeys([*registry.get("common_material_ids", []), *material_ids]))
    unknown = [material_id for material_id in selected if material_id not in materials]
    if unknown:
        raise ValueError(f"unknown material palette ids: {', '.join(unknown)}")
    colors = {
        _hex_to_rgb(color)
        for material_id in selected
        for color in materials[material_id].get("colors", [])
    }
    tone_ramps = {
        material_id: {
            "tone_ramp": materials[material_id].get("tone_ramp", []),
            "minimum_tone_roles": int(materials[material_id].get("minimum_tone_roles", 0)),
            "audit_tone_usage": bool(materials[material_id].get("audit_tone_usage", False)),
        }
        for material_id in selected
    }
    return colors, {
        "palette_version": registry["palette_version"],
        "approval_status": registry["approval_status"],
        "material_ids": selected,
        "registered_color_count": len(colors),
        "registry": str(registry_path),
        "material_tone_ramps": tone_ramps,
    }


def resolve_asset_contract(profile: dict, asset_class: str, task_contract: dict | None = None) -> dict:
    try:
        spec = dict(profile["asset_classes"][asset_class])
    except KeyError as exc:
        choices = ", ".join(sorted(profile.get("asset_classes", {})))
        raise ValueError(f"unknown asset class {asset_class!r}; choose from: {choices}") from exc
    task_contract = task_contract or {}
    policy = spec["dimension_policy"]
    if policy == "exact":
        dimensions = list(spec["dimensions"])
        if task_contract.get("dimensions") not in (None, dimensions):
            raise ValueError(f"{asset_class} dimensions are fixed at {dimensions}")
    else:
        dimensions = task_contract.get("dimensions")
        if not dimensions or len(dimensions) != 2:
            raise ValueError(f"{asset_class} requires task_contract dimensions [width, height]")
        dimensions = [int(value) for value in dimensions]
        if policy == "task_exact_within_range":
            minimum, maximum = spec["min_dimensions"], spec["max_dimensions"]
            if any(value < low or value > high for value, low, high in zip(dimensions, minimum, maximum)):
                raise ValueError(
                    f"{asset_class} dimensions {dimensions} outside range {minimum}..{maximum}"
                )
            alignment = int(spec.get("alignment", 1))
            if any(value % alignment for value in dimensions):
                raise ValueError(f"{asset_class} dimensions must align to {alignment}px")
    if spec.get("anchor") is not None and task_contract.get("anchor") not in (None, spec["anchor"]):
        raise ValueError(f"{asset_class} anchor is fixed at {spec['anchor']}")
    anchor = task_contract.get("anchor", spec.get("anchor", [dimensions[0] // 2, dimensions[1]]))
    if len(anchor) != 2:
        raise ValueError("anchor must be [x, y]")
    resolved = dict(spec)
    resolved.update(
        {
            "asset_class": asset_class,
            "dimensions": dimensions,
            "anchor": [int(anchor[0]), int(anchor[1])],
            "anchor_coordinate_kind": task_contract.get(
                "anchor_coordinate_kind", spec.get("anchor_coordinate_kind", "canvas_boundary")
            ),
            "tileable": bool(task_contract.get("tileable", spec.get("tileable", False))),
        }
    )
    if "max_colors" in task_contract:
        resolved["max_colors"] = int(task_contract["max_colors"])
    return resolved


def _exact_repeat_3x3(array: np.ndarray, tile_dimensions: list[int]) -> bool:
    tile_width, tile_height = tile_dimensions
    reference = array[:tile_height, :tile_width]
    return all(
        np.array_equal(
            reference,
            array[row * tile_height : (row + 1) * tile_height, column * tile_width : (column + 1) * tile_width],
        )
        for row in range(3)
        for column in range(3)
    )


def audit_native_png(
    image_path: str | Path,
    profile: dict,
    profile_path: str | Path,
    contract: dict,
    material_ids: Iterable[str],
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    manual_review = [
        "native pixel authorship / no resized generated reference",
        "no anti-aliasing, blurred edges, smooth gradients, or half-pixel geometry",
        "upper-left key light and lower-right shadow logic",
        "orthographic projection, north-up orientation, and legal planning angles",
    ]
    image_path = Path(image_path)
    try:
        with Image.open(image_path) as opened:
            source_format = opened.format
            image = opened.convert("RGBA")
    except Exception as exc:  # Pillow supplies format-specific detail.
        return {
            "schema_version": 1,
            "verdict": "REJECT",
            "errors": [f"unreadable image: {exc}"],
            "warnings": [],
            "manual_review_required": manual_review,
            "checks": {},
        }
    if source_format != "PNG" or image_path.suffix.lower() != ".png":
        errors.append("file must be PNG")
    expected_size = tuple(contract["dimensions"])
    if image.size != expected_size:
        errors.append(f"dimensions {image.size} do not match contract {expected_size}")
    array = np.asarray(image)
    alpha_values = sorted(int(value) for value in np.unique(array[..., 3]))
    if not set(alpha_values) <= set(profile["alpha"]["allowed_values"]):
        errors.append(f"alpha values must be only 0/255; found {alpha_values[:16]}")
    opaque = array[..., 3] == 255
    if not opaque.any():
        errors.append("asset has no opaque pixels")
    opaque_colors = {tuple(int(channel) for channel in color) for color in array[..., :3][opaque]}
    try:
        allowed_colors, palette_meta = material_colors(profile, profile_path, material_ids)
    except ValueError as exc:
        errors.append(str(exc))
        allowed_colors, palette_meta = set(), {
            "palette_version": profile["palette"]["palette_version"],
            "approval_status": profile["palette"]["approval_status"],
            "material_ids": list(material_ids),
            "registered_color_count": 0,
        }
    unregistered = sorted(opaque_colors - allowed_colors)
    if unregistered:
        errors.append(f"{len(unregistered)} opaque RGB colors are outside declared material sub-palettes")
    tone_usage = {}
    for material_id in dict.fromkeys(material_ids):
        ramp_meta = palette_meta.get("material_tone_ramps", {}).get(material_id, {})
        ramp = ramp_meta.get("tone_ramp", [])
        used_roles = [entry["role"] for entry in ramp if _hex_to_rgb(entry["color"]) in opaque_colors]
        minimum = int(ramp_meta.get("minimum_tone_roles", 0))
        tone_usage[material_id] = {
            "used_roles": used_roles,
            "used_role_count": len(used_roles),
            "minimum_tone_roles": minimum,
        }
        if ramp_meta.get("audit_tone_usage") and len(used_roles) < minimum:
            warnings.append(
                f"material {material_id} uses {len(used_roles)}/{minimum} required tone roles; "
                "flat-shading review required"
            )
    color_count = len(opaque_colors)
    if contract.get("max_colors") is not None and color_count > int(contract["max_colors"]):
        errors.append(f"opaque color count {color_count} exceeds max {contract['max_colors']}")
    typical = contract.get("typical_color_range")
    if typical and not int(typical[0]) <= color_count <= int(typical[1]):
        warnings.append(f"opaque color count {color_count} is outside typical range {typical}")
    if contract["asset_class"] == "material_review_sample" and image.size == expected_size:
        if not _exact_repeat_3x3(array, contract["source_tile_dimensions"]):
            errors.append("material review sample is not an exact 3x3 repeat of one 64x64 tile")
    bbox = image.getchannel("A").getbbox()
    if contract["asset_class"] == "character_frame" and bbox and bbox[3] != image.height:
        errors.append("character feet must reach the y=96 canvas boundary (last opaque row y=95)")
    if not palette_is_approved(profile["palette"]["approval_status"]):
        warnings.append("project RGB palette is provisional; runtime release remains blocked")
    return {
        "schema_version": 1,
        "profile_id": profile["profile_id"],
        "asset_class": contract["asset_class"],
        "verdict": "REJECT" if errors else ("REVIEW" if warnings or manual_review else "APPROVE"),
        "errors": errors,
        "warnings": warnings,
        "manual_review_required": manual_review,
        "checks": {
            "format": source_format,
            "dimensions": list(image.size),
            "expected_dimensions": list(expected_size),
            "alpha_values": alpha_values,
            "opaque_color_count": color_count,
            "unregistered_colors": [list(color) for color in unregistered[:64]],
            "content_bbox": list(bbox) if bbox else None,
            "palette": palette_meta,
            "material_tone_usage": tone_usage,
        },
    }


def validate_import_contract(import_contract: dict, tileable: bool) -> list[str]:
    errors = []
    expected = {
        "texture_filter": "nearest",
        "mipmaps": False,
        "integer_position": True,
        "integer_scale": True,
    }
    for field, value in expected.items():
        if import_contract.get(field) != value:
            errors.append(f"import_contract.{field} must be {value!r}")
    if import_contract.get("compression") not in {"lossless", "project_approved_pixel_safe"}:
        errors.append("import_contract.compression is not pixel-safe")
    if bool(import_contract.get("repeat")) != bool(tileable):
        errors.append("import_contract.repeat must match the declared tileable contract")
    for field in ("collision_source", "occlusion_source", "navigation_source"):
        if import_contract.get(field) == "png_alpha":
            errors.append(f"{field} cannot be inferred from PNG alpha")
    return errors
