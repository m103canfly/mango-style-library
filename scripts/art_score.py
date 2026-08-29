#!/usr/bin/env python3
"""Compute the versioned Mango/Tingen art-review score from evidenced grades."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


WEIGHTS = {
    "technical_integrity": 20,
    "silhouette_composition": 20,
    "style_palette": 20,
    "category_regional_identity": 15,
    "scale_alignment": 15,
    "motion_continuity": 10,
}


def score_review(payload: dict) -> dict:
    errors: list[str] = []
    dimensions = payload.get("dimensions", {})
    weighted: dict[str, dict] = {}
    for dimension, weight in WEIGHTS.items():
        record = dimensions.get(dimension)
        if not isinstance(record, dict):
            errors.append(f"missing dimension {dimension}")
            continue
        grade = record.get("grade")
        if not isinstance(grade, (int, float)) or not 0 <= grade <= 5:
            errors.append(f"{dimension}.grade must be in [0,5]")
            continue
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{dimension}.evidence must contain at least one evidence reference")
        points = float(grade) / 5.0 * weight
        weighted[dimension] = {"grade": grade, "weight": weight, "points": round(points, 2), "evidence": evidence}
    if errors:
        raise ValueError("; ".join(errors))
    score = round(sum(record["points"] for record in weighted.values()), 2)
    critical = list(dict.fromkeys(payload.get("critical_failures", [])))
    verdict = "REJECT" if critical or score < 75 else ("REVIEW" if score < 90 else "APPROVE")
    return {
        "schema_version": 1,
        "asset_id": payload.get("asset_id"),
        "profile_id": payload.get("profile_id", "tingen_pixel_v3_hd"),
        "review_profile": payload.get("review_profile", "tingen-standard-v1"),
        "review_score": score,
        "review_verdict": verdict,
        "critical_failures": critical,
        "dimensions": weighted,
        "reviewer": payload.get("reviewer", "unassigned"),
        "reviewed_at": payload.get("reviewed_at") or datetime.now(timezone.utc).isoformat(),
        "gold_anchor_eligible": verdict == "APPROVE" and score >= 92 and not critical,
        "note": "Gold Anchor promotion still requires explicit human approval; this score does not self-promote an asset.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute an evidenced 100-point art review")
    parser.add_argument("input", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = score_review(json.loads(args.input.read_text(encoding="utf-8")))
    except ValueError as exc:
        parser.error(str(exc))
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(payload, encoding="utf-8")
    print(payload)
    return {"APPROVE": 0, "REVIEW": 1, "REJECT": 2}[result["review_verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
