#!/usr/bin/env python3
"""Validate Style Anchor Pack authority, status, and file provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_MANIFEST = Path("assets/anchors/style-anchor-manifest.yaml")
VALID_ANCHOR_STATUS = {"candidate", "approved", "retired"}
VALID_CATEGORY_STATUS = {"needs-production", "in-review", "approved"}


def validate(manifest_path: Path, repository_root: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []
    approved_total = 0
    for category_name, category in manifest["categories"].items():
        if category.get("status") not in VALID_CATEGORY_STATUS:
            errors.append(f"{category_name}: invalid category status {category.get('status')!r}")
        required = set(category.get("required_slots", []))
        approved_slots = set()
        seen_ids = set()
        for anchor in category.get("anchors", []):
            anchor_id = anchor.get("id")
            if not anchor_id or anchor_id in seen_ids:
                errors.append(f"{category_name}: missing or duplicate anchor id {anchor_id!r}")
            seen_ids.add(anchor_id)
            status = anchor.get("status")
            if status not in VALID_ANCHOR_STATUS:
                errors.append(f"{category_name}/{anchor_id}: invalid status {status!r}")
            path = anchor.get("path")
            if not path or not (repository_root / path).is_file():
                errors.append(f"{category_name}/{anchor_id}: missing file {path!r}")
            if path and "scene-bible" in Path(path).parts:
                errors.append(f"{category_name}/{anchor_id}: Scene Bible image cannot be a Gold Anchor")
            if status == "approved":
                approved_total += 1
                approved_slots.add(anchor.get("slot"))
                for field in ("version", "review_score", "reviewed_at", "reviewer"):
                    if anchor.get(field) in (None, ""):
                        errors.append(f"{category_name}/{anchor_id}: approved anchor lacks {field}")
        missing_slots = sorted(required - approved_slots)
        if missing_slots:
            warnings.append(f"{category_name}: approved slots missing: {', '.join(missing_slots)}")
        if len(approved_slots) < int(category.get("minimum_approved", 0)):
            warnings.append(
                f"{category_name}: {len(approved_slots)}/{category.get('minimum_approved')} minimum approved anchors"
            )
        if category.get("status") == "approved" and missing_slots:
            errors.append(f"{category_name}: category marked approved while required slots are missing")
    return {
        "valid": not errors,
        "release_ready": not errors and not warnings,
        "approved_anchor_count": approved_total,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate category Gold Anchor authority")
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true", help="fail when approved slots are missing")
    parser.add_argument("--json", dest="json_path", type=Path, default=None)
    args = parser.parse_args()
    result = validate(args.manifest, args.root)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_path:
        args.json_path.write_text(payload, encoding="utf-8")
    print(payload)
    if result["errors"]:
        return 2
    if args.strict and result["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
