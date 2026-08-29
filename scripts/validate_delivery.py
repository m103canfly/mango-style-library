#!/usr/bin/env python3
"""Independently revalidate a packaged Tingen asset directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from tingen_contract import (
    DEFAULT_PROFILE,
    audit_native_png,
    load_json,
    resolve_asset_contract,
    sha256_file,
    validate_import_contract,
)


SAFE_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


REQUIRED_MANIFEST_FIELDS = {
    "asset_id", "asset_name", "profile_id", "style_version", "asset_class", "district_id",
    "dimensions", "facing", "anchor", "anchor_coordinate_kind", "material_ids", "palette_version",
    "palette_approval_status", "alpha_policy", "source_status", "sha256", "lifecycle_status",
}


def validate_delivery(directory: str | Path, profile_path: str | Path = DEFAULT_PROFILE) -> dict:
    directory = Path(directory)
    profile_path = Path(profile_path)
    profile = load_json(profile_path)
    errors: list[str] = []
    warnings: list[str] = []
    for name in ("manifest.json", "audit.json", "source_reference.json", "import_contract.json"):
        if not (directory / name).is_file():
            errors.append(f"missing {name}")
    if errors:
        return {"valid": False, "runtime_ready": False, "errors": errors, "warnings": warnings}
    manifest = load_json(directory / "manifest.json")
    missing_fields = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing_fields:
        errors.append("manifest missing fields: " + ", ".join(missing_fields))
    asset_name = manifest.get("asset_name", "")
    if not asset_name or any(character not in SAFE_NAME_CHARS for character in asset_name) or asset_name in {".", ".."}:
        errors.append("manifest asset_name is unsafe")
    if manifest.get("profile_id") != profile["profile_id"]:
        errors.append("manifest profile_id does not match active profile")
    asset_id = manifest.get("asset_id", "")
    if not asset_id or any(character not in SAFE_NAME_CHARS for character in asset_id) or asset_id in {".", ".."}:
        errors.append("manifest asset_id is unsafe")
    if manifest.get("style_version") != profile["style_version"]:
        errors.append("manifest style_version does not match active profile")
    if manifest.get("alpha_policy") != profile["alpha"]["policy"]:
        errors.append("manifest alpha_policy does not match active profile")
    if manifest.get("palette_version") != profile["palette"]["palette_version"]:
        errors.append("manifest palette_version does not match active profile")
    if manifest.get("palette_approval_status") != profile["palette"]["approval_status"]:
        errors.append("manifest palette_approval_status does not match active profile")
    if manifest.get("anchor_coordinate_kind") != "canvas_boundary":
        errors.append("manifest anchor_coordinate_kind must be canvas_boundary")
    one_x = directory / f"{asset_name}_1x.png"
    four_x = directory / f"{asset_name}_4x.png"
    if not one_x.is_file():
        errors.append(f"missing {one_x.name}")
    if not four_x.is_file():
        errors.append(f"missing {four_x.name}")
    if errors:
        return {"valid": False, "runtime_ready": False, "errors": errors, "warnings": warnings}
    try:
        task_contract = {"dimensions": manifest["dimensions"], "anchor": manifest["anchor"]}
        contract = resolve_asset_contract(profile, manifest["asset_class"], task_contract)
    except (KeyError, ValueError) as exc:
        errors.append(str(exc))
        return {"valid": False, "runtime_ready": False, "errors": errors, "warnings": warnings}
    audit = audit_native_png(one_x, profile, profile_path, contract, manifest.get("material_ids", []))
    errors.extend(audit["errors"])
    warnings.extend(audit["warnings"])
    if sha256_file(one_x) != manifest.get("sha256"):
        errors.append("manifest sha256 does not match 1x PNG")
    with Image.open(one_x) as source, Image.open(four_x) as preview:
        one = np.asarray(source.convert("RGBA"))
        four = np.asarray(preview.convert("RGBA"))
    expected_preview = np.repeat(np.repeat(one, 4, axis=0), 4, axis=1)
    if four.shape != expected_preview.shape or not np.array_equal(four, expected_preview):
        errors.append("4x preview is not an exact nearest-neighbor integer enlargement")
    import_contract = load_json(directory / "import_contract.json")
    errors.extend(validate_import_contract(import_contract, contract["tileable"]))
    source_reference = load_json(directory / "source_reference.json")
    if source_reference.get("generated_hd_reference_directly_resized") is not False:
        errors.append("generated HD reference was directly resized into delivery")
    if manifest.get("source_status") not in profile["source_policy"]["delivery_sources"]:
        errors.append("manifest source_status is not delivery-eligible")
    if manifest.get("asset_class") == "character_frame" and manifest.get("facing") not in contract["facings"]:
        errors.append("character_frame facing is invalid")
    if manifest.get("lifecycle_status") != "candidate_pending_user_1x_review":
        review = manifest.get("review") or {}
        if review.get("review_verdict") != "APPROVE" or float(review.get("review_score") or 0) < 90:
            errors.append("non-candidate lifecycle lacks an APPROVE review score >=90")
    runtime_validation = import_contract.get("runtime_validation", {})
    runtime_passed = runtime_validation.get("status") == "passed" and all(
        runtime_validation.get(field) is True
        for field in ("entrance", "collision", "navigation", "same_screen_scale")
    )
    palette_approved = profile["palette"]["approval_status"] == "approved"
    runtime_ready = not errors and runtime_passed and palette_approved
    if manifest.get("lifecycle_status") == "runtime_ready" and not runtime_ready:
        errors.append("manifest claims runtime_ready without palette and Godot runtime approval")
        runtime_ready = False
    return {
        "schema_version": 1,
        "profile_id": profile["profile_id"],
        "valid": not errors,
        "runtime_ready": runtime_ready,
        "errors": errors,
        "warnings": list(dict.fromkeys(warnings)),
        "technical_audit": audit,
        "runtime_validation_passed": runtime_passed,
        "palette_approved": palette_approved,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Tingen standard delivery directory")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--json", dest="json_path", type=Path, default=None)
    args = parser.parse_args()
    result = validate_delivery(args.directory, args.profile)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
