#!/usr/bin/env python3
"""Audit animation-frame geometry after shared-transform export.

Metrics are deliberately mechanical and do not judge whether an animation looks
good. They detect scale/origin regressions: bbox variance, centroid drift, foot
baseline drift, and adjacent silhouette overlap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image


DEFAULT_THRESHOLDS = {
    "bbox_width_variance": 0.18,
    "bbox_height_variance": 0.10,
    "centroid_drift_px": 3.0,
    "foot_baseline_drift_px": 1.0,
    "silhouette_overlap_min": 0.52,
}


def split_sheet(path: str | Path, hframes: int, vframes: int, row: int | None = None) -> list[Image.Image]:
    image = Image.open(path).convert("RGBA")
    if hframes <= 0 or vframes <= 0:
        raise ValueError("hframes and vframes must be positive")
    if image.width % hframes or image.height % vframes:
        raise ValueError("sheet dimensions must be divisible by hframes/vframes")
    frame_width, frame_height = image.width // hframes, image.height // vframes
    rows = range(vframes) if row is None else [row]
    if any(index < 0 or index >= vframes for index in rows):
        raise ValueError("row is outside the sprite sheet")
    return [
        image.crop(
            (
                column * frame_width,
                row_index * frame_height,
                (column + 1) * frame_width,
                (row_index + 1) * frame_height,
            )
        )
        for row_index in rows
        for column in range(hframes)
    ]


def _mask_and_geometry(image: Image.Image, alpha_threshold: int) -> dict:
    alpha = np.asarray(image.convert("RGBA"))[..., 3]
    mask = alpha >= alpha_threshold
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("empty frame after alpha threshold")
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return {
        "mask": mask,
        "bbox": bbox,
        "width": bbox[2] - bbox[0],
        "height": bbox[3] - bbox[1],
        "centroid": (float(xs.mean()), float(ys.mean())),
        "foot_baseline": bbox[3] - 1,
        "area": int(mask.sum()),
    }


def _shift_mask(mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
    shifted = np.zeros_like(mask)
    height, width = mask.shape
    src_x0, src_x1 = max(0, -dx), min(width, width - dx)
    src_y0, src_y1 = max(0, -dy), min(height, height - dy)
    dst_x0, dst_x1 = src_x0 + dx, src_x1 + dx
    dst_y0, dst_y1 = src_y0 + dy, src_y1 + dy
    if src_x0 < src_x1 and src_y0 < src_y1:
        shifted[dst_y0:dst_y1, dst_x0:dst_x1] = mask[src_y0:src_y1, src_x0:src_x1]
    return shifted


def _iou(left: np.ndarray, right: np.ndarray) -> float:
    union = np.logical_or(left, right).sum()
    return float(np.logical_and(left, right).sum() / union) if union else 1.0


def audit_frames(
    frames: Sequence[Image.Image],
    alpha_threshold: int = 64,
    thresholds: dict | None = None,
) -> dict:
    if len(frames) < 2:
        raise ValueError("motion audit requires at least two frames")
    sizes = {frame.size for frame in frames}
    if len(sizes) != 1:
        raise ValueError("all frames must share the same output canvas")
    geometry = [_mask_and_geometry(frame, alpha_threshold) for frame in frames]
    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        limits.update(thresholds)

    widths = np.asarray([item["width"] for item in geometry], dtype=float)
    heights = np.asarray([item["height"] for item in geometry], dtype=float)
    centroids = np.asarray([item["centroid"] for item in geometry], dtype=float)
    baselines = np.asarray([item["foot_baseline"] for item in geometry], dtype=float)
    median_centroid = np.median(centroids, axis=0)

    overlaps = []
    for left, right in zip(geometry, geometry[1:]):
        dx = round(left["centroid"][0] - right["centroid"][0])
        dy = left["foot_baseline"] - right["foot_baseline"]
        overlaps.append(_iou(left["mask"], _shift_mask(right["mask"], dx, dy)))

    metrics = {
        "bbox_width_variance": float((widths.max() - widths.min()) / max(1.0, np.median(widths))),
        "bbox_height_variance": float((heights.max() - heights.min()) / max(1.0, np.median(heights))),
        "centroid_drift_px": float(np.linalg.norm(centroids - median_centroid, axis=1).max()),
        "foot_baseline_drift_px": float(baselines.max() - baselines.min()),
        "silhouette_overlap_min": float(min(overlaps)),
    }
    failures = []
    reject_failures = []
    for key in ("bbox_width_variance", "bbox_height_variance", "centroid_drift_px", "foot_baseline_drift_px"):
        if metrics[key] > limits[key]:
            failures.append(key)
        if metrics[key] > limits[key] * 2:
            reject_failures.append(key)
    if metrics["silhouette_overlap_min"] < limits["silhouette_overlap_min"]:
        failures.append("silhouette_overlap_min")
    if metrics["silhouette_overlap_min"] < max(0.0, limits["silhouette_overlap_min"] - 0.20):
        reject_failures.append("silhouette_overlap_min")

    verdict = "REJECT" if reject_failures else ("REVIEW" if failures else "APPROVE")
    penalty = 0.0
    for key in ("bbox_width_variance", "bbox_height_variance", "centroid_drift_px", "foot_baseline_drift_px"):
        penalty += min(20.0, 10.0 * metrics[key] / max(limits[key], 1e-9))
    overlap_deficit = max(0.0, limits["silhouette_overlap_min"] - metrics["silhouette_overlap_min"])
    penalty += min(20.0, overlap_deficit * 100.0)
    return {
        "schema_version": 1,
        "verdict": verdict,
        "score": max(0, round(100 - penalty)),
        "frame_count": len(frames),
        "canvas": list(frames[0].size),
        "alpha_threshold": alpha_threshold,
        "thresholds": limits,
        "metrics": {key: round(value, 4) for key, value in metrics.items()},
        "failures": failures,
        "reject_failures": reject_failures,
        "frames": [
            {
                "bbox": list(item["bbox"]),
                "centroid": [round(value, 3) for value in item["centroid"]],
                "foot_baseline": item["foot_baseline"],
                "area": item["area"],
            }
            for item in geometry
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit animation geometry and silhouette stability")
    parser.add_argument("frames", nargs="*")
    parser.add_argument("--sheet", default=None)
    parser.add_argument("--hframes", type=int, default=None)
    parser.add_argument("--vframes", type=int, default=1)
    parser.add_argument("--row", type=int, default=None)
    parser.add_argument("--alpha-threshold", type=int, default=64)
    parser.add_argument("--json", dest="json_path", default=None)
    args = parser.parse_args()
    if args.sheet:
        if not args.hframes:
            parser.error("--sheet requires --hframes")
        frames = split_sheet(args.sheet, args.hframes, args.vframes, args.row)
    else:
        if len(args.frames) < 2:
            parser.error("provide at least two frame PNGs or use --sheet")
        frames = [Image.open(path).convert("RGBA") for path in args.frames]
    result = audit_frames(frames, alpha_threshold=args.alpha_threshold)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_path:
        Path(args.json_path).write_text(payload, encoding="utf-8")
    print(payload)
    return {"APPROVE": 0, "REVIEW": 1, "REJECT": 2}[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
