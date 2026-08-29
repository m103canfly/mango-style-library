#!/usr/bin/env python3
"""Package one native 1x Tingen asset without resampling the runtime PNG."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from PIL import Image

from tingen_contract import (
    DEFAULT_PROFILE,
    audit_native_png,
    load_json,
    resolve_asset_contract,
    sha256_file,
)


SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def package_asset(args: argparse.Namespace) -> Path:
    profile_path = Path(args.profile)
    profile = load_json(profile_path)
    task_contract = load_json(args.task_contract) if args.task_contract else None
    contract = resolve_asset_contract(profile, args.asset_class, task_contract)
    if not SAFE_NAME.fullmatch(args.asset_name):
        raise ValueError("asset-name may contain only ASCII letters, digits, dot, underscore, and hyphen")
    if not SAFE_NAME.fullmatch(args.asset_id) or args.asset_id in {".", ".."}:
        raise ValueError("asset-id may contain only ASCII letters, digits, dot, underscore, and hyphen")
    if args.source_status not in profile["source_policy"]["delivery_sources"]:
        raise ValueError("generated HD references cannot be packaged as native 1x delivery assets")
    if args.asset_class == "character_frame" and args.facing not in contract["facings"]:
        raise ValueError(f"character_frame requires one of these facings: {', '.join(contract['facings'])}")
    if args.lifecycle_status == "runtime_ready":
        raise ValueError("package creation cannot claim runtime_ready before independent Godot validation")
    review = load_json(args.review_json) if args.review_json else None
    if args.lifecycle_status != "candidate_pending_user_1x_review":
        if not review:
            raise ValueError("approved/runtime-validation lifecycle requires --review-json")
        if review.get("review_verdict") != "APPROVE" or float(review.get("review_score", 0)) < 90:
            raise ValueError("review-json must record APPROVE with score >=90")
        if review.get("critical_failures"):
            raise ValueError("review-json still contains critical failures")
    audit = audit_native_png(
        args.input,
        profile,
        profile_path,
        contract,
        args.material_id,
    )
    if audit["errors"]:
        raise ValueError("native 1x audit failed: " + "; ".join(audit["errors"]))

    destination = Path(args.output_root) / args.asset_id
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty delivery directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    one_x = destination / f"{args.asset_name}_1x.png"
    four_x = destination / f"{args.asset_name}_4x.png"
    shutil.copy2(args.input, one_x)
    with Image.open(one_x) as image:
        rgba = image.convert("RGBA")
        rgba.resize((rgba.width * 4, rgba.height * 4), Image.Resampling.NEAREST).save(four_x)

    manifest = {
        "schema_version": 1,
        "asset_id": args.asset_id,
        "asset_name": args.asset_name,
        "profile_id": profile["profile_id"],
        "style_version": profile["style_version"],
        "asset_class": args.asset_class,
        "district_id": args.district_id,
        "dimensions": contract["dimensions"],
        "facing": args.facing,
        "anchor": contract["anchor"],
        "anchor_coordinate_kind": contract["anchor_coordinate_kind"],
        "material_ids": list(dict.fromkeys(args.material_id)),
        "palette_version": profile["palette"]["palette_version"],
        "palette_approval_status": profile["palette"]["approval_status"],
        "alpha_policy": profile["alpha"]["policy"],
        "source_status": args.source_status,
        "sha256": sha256_file(one_x),
        "lifecycle_status": args.lifecycle_status,
        "runtime_ready": False,
        "task_contract": str(args.task_contract) if args.task_contract else None,
        "review": {
            "review_score": review.get("review_score"),
            "review_verdict": review.get("review_verdict"),
            "reviewer": review.get("reviewer"),
            "reviewed_at": review.get("reviewed_at"),
            "review_profile": review.get("review_profile"),
        } if review else None,
    }
    source_reference = {
        "schema_version": 1,
        "source_path": str(Path(args.input)),
        "source_sha256": sha256_file(args.input),
        "source_status": args.source_status,
        "reference_ids": args.reference_id,
        "generated_hd_reference_directly_resized": False,
    }
    import_contract = {
        "schema_version": 1,
        "texture_filter": "nearest",
        "mipmaps": False,
        "compression": "lossless",
        "repeat": contract["tileable"],
        "integer_position": True,
        "integer_scale": True,
        "collision_source": "explicit_project_data",
        "occlusion_source": "explicit_project_data",
        "navigation_source": "explicit_project_data",
        "runtime_validation": {
            "entrance": False,
            "collision": False,
            "navigation": False,
            "same_screen_scale": False,
            "status": "pending"
        }
    }
    audit["packaging"] = {
        "runtime_png_resampled": False,
        "preview_scale": 4,
        "preview_resample": "nearest",
        "runtime_validation_pending": True,
    }
    write_json(destination / "manifest.json", manifest)
    write_json(destination / "audit.json", audit)
    write_json(destination / "source_reference.json", source_reference)
    write_json(destination / "import_contract.json", import_contract)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Package a native 1x Tingen project asset")
    parser.add_argument("input", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--asset-name", required=True)
    parser.add_argument("--asset-class", required=True)
    parser.add_argument("--district-id", required=True)
    parser.add_argument("--facing", default="not_applicable")
    parser.add_argument("--material-id", action="append", required=True)
    parser.add_argument("--source-status", required=True)
    parser.add_argument("--reference-id", action="append", default=[])
    parser.add_argument("--task-contract", type=Path, default=None)
    parser.add_argument("--review-json", type=Path, default=None)
    parser.add_argument(
        "--lifecycle-status",
        choices=["candidate_pending_user_1x_review", "approved_1x", "runtime_validation_pending"],
        default="candidate_pending_user_1x_review",
    )
    args = parser.parse_args()
    try:
        destination = package_asset(args)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
