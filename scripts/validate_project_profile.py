#!/usr/bin/env python3
"""Validate the Tingen project profile and combined production release gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from palette_remap import build_palette, load_palette_config
from tingen_contract import DEFAULT_PROFILE, load_json, material_colors, palette_is_approved, resolve_project_path
from validate_anchor_pack import DEFAULT_MANIFEST, validate as validate_anchor_pack


def validate(profile_path: Path, repository_root: Path) -> dict:
    errors: list[str] = []
    blockers: list[str] = []
    profile = load_json(profile_path)
    for field in ("profile_id", "style_version", "asset_classes", "animation", "godot_import", "delivery"):
        if field not in profile:
            errors.append(f"profile missing {field}")
    palette_config_path = resolve_project_path(profile_path, profile["palette"]["registry"])
    material_registry_path = resolve_project_path(profile_path, profile["palette"]["material_registry"])
    if not palette_config_path.is_file():
        errors.append(f"missing palette registry {palette_config_path}")
    if not material_registry_path.is_file():
        errors.append(f"missing material registry {material_registry_path}")
    if not errors:
        palette_config = load_palette_config(palette_config_path)
        palette, _ = build_palette(palette_config, region=profile["palette"]["region"])
        registry = load_json(material_registry_path)
        if palette_config.get("approval_status") != profile["palette"].get("approval_status"):
            errors.append("profile and palette registry approval_status do not match")
        if registry.get("approval_status") != profile["palette"].get("approval_status"):
            errors.append("profile and material registry approval_status do not match")
        if palette_config.get("derivation", {}).get("runtime_sampling") is not False:
            errors.append("template palette must explicitly prohibit runtime sampling")
        if registry.get("composite_remap_policy") != "material_masks_required_no_global_nearest_color":
            errors.append("material registry must prohibit whole-composite nearest-color remapping")
        all_material_ids = list(registry["materials"])
        registered, _ = material_colors(profile, profile_path, all_material_ids)
        base_colors = {tuple(int(channel) for channel in color) for color in palette}
        outside = sorted(registered - base_colors)
        if outside:
            errors.append(f"material registry contains {len(outside)} colors outside Master + Region palette")
        for material_id, material in registry["materials"].items():
            colors = set(material.get("colors", []))
            ramp = material.get("tone_ramp", [])
            ramp_colors = [entry.get("color") for entry in ramp]
            ramp_roles = [entry.get("role") for entry in ramp]
            minimum = int(material.get("minimum_tone_roles", 0))
            if not set(ramp_colors) <= colors:
                errors.append(f"material {material_id} tone_ramp contains colors outside its sub-palette")
            if len(ramp_colors) != len(set(ramp_colors)) or len(ramp_roles) != len(set(ramp_roles)):
                errors.append(f"material {material_id} tone_ramp contains duplicate color or role entries")
            if material.get("audit_tone_usage") and (minimum < 3 or len(ramp) < minimum):
                errors.append(f"material {material_id} lacks the minimum anti-flat tone ramp")
    if not palette_is_approved(profile["palette"].get("approval_status")):
        blockers.append("Tingen RGB palette is provisional and has not been project-approved")
    anchor_result = validate_anchor_pack(repository_root / DEFAULT_MANIFEST, repository_root)
    if not anchor_result["valid"]:
        errors.extend(f"anchor pack: {error}" for error in anchor_result["errors"])
    if not anchor_result["release_ready"]:
        blockers.append("Category Gold Anchor Pack is not release-ready")
    required_delivery = set(profile["delivery"].get("required_files", []))
    expected_delivery = {
        "<asset_name>_1x.png", "<asset_name>_4x.png", "manifest.json", "audit.json",
        "source_reference.json", "import_contract.json",
    }
    if required_delivery != expected_delivery:
        errors.append("profile delivery.required_files does not match the project standard")
    return {
        "schema_version": 1,
        "profile_id": profile.get("profile_id"),
        "valid": not errors,
        "release_ready": not errors and not blockers,
        "errors": errors,
        "blockers": blockers,
        "anchor_pack": anchor_result,
        "palette_approval_status": profile["palette"].get("approval_status"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Tingen profile and release blockers")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", dest="json_path", type=Path, default=None)
    args = parser.parse_args()
    result = validate(args.profile, args.root.resolve())
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(payload, encoding="utf-8")
    print(payload)
    if result["errors"]:
        return 2
    if args.strict and result["blockers"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
