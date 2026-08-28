#!/usr/bin/env python3
"""Import the supplied nine-region scene packages into the Scene Bible.

The source 2048x1152 gameplay mockups contain HUD and a generator watermark.
They remain external source archives. This importer writes:
  * 90 central, HUD-free visual anchors (compressed PNG);
  * 9 regional review contact sheets;
  * one YAML-1.2-compatible JSON manifest with source hashes and authority limits;
  * the supplied 90-row review ledger for provenance.

Example:
    python scripts/import_scene_bible.py --source-dir /path/to/scene-zips
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

from PIL import Image


CROP_NORM = (0.25, 0.0, 0.835, 0.80)
VISUAL_SIZE = (640, 493)
VISUAL_COLORS = 192
REVIEW_WIDTH = 1024
REVIEW_COLORS = 128

REGIONS = [
    {
        "slug": "loen",
        "name": "鲁恩王国",
        "zip": "场景包_鲁恩王国.zip",
        "features": ["red brick", "cream stone", "blue-grey slate", "gas lamps", "Georgian and Gothic civic forms", "temperate greenery"],
    },
    {
        "slug": "intis",
        "name": "因蒂斯共和国",
        "zip": "场景包_因蒂斯共和国.zip",
        "features": ["pale limestone", "formal axes", "French civic classicism", "ornamental gardens", "urban boulevards", "republican emblems"],
    },
    {
        "slug": "feysac",
        "name": "弗萨克帝国",
        "zip": "场景包_弗萨克帝国.zip",
        "features": ["snow and frost", "heavy masonry", "steep roofs", "onion-dome accents", "dark timber", "imperial monumental scale"],
    },
    {
        "slug": "feynapotter",
        "name": "费内波特王国",
        "zip": "场景包_费内波特王国.zip",
        "features": ["warm stucco", "terracotta", "Mediterranean planting", "arcades", "flower-rich streets", "sunlit stone"],
    },
    {
        "slug": "segar",
        "name": "塞加尔诸邦",
        "zip": "场景包_塞加尔诸邦.zip",
        "features": ["north-central European townscape", "restrained masonry", "gabled roofs", "muted greens", "merchant civic identity", "compact streets"],
    },
    {
        "slug": "balam",
        "name": "拜朗帝国",
        "zip": "场景包_拜朗帝国.zip",
        "features": ["tropical vegetation", "colonial civic buildings", "bright plaster", "deep shade", "market density", "river and port motifs"],
    },
    {
        "slug": "highland",
        "name": "高地王国",
        "zip": "场景包_高地王国.zip",
        "features": ["mountain stone", "Andean massing", "terraced terrain", "earth pigments", "high-altitude vegetation", "river-crossing infrastructure"],
    },
    {
        "slug": "pas",
        "name": "帕斯王国",
        "zip": "场景包_帕斯王国.zip",
        "features": ["pampas landscape", "ranch compounds", "livestock economy", "broad low buildings", "warm timber", "open horizons"],
    },
    {
        "slug": "hagati",
        "name": "哈加提草原",
        "zip": "场景包_哈加提草原.zip",
        "features": ["steppe grassland", "felt tents", "portable ornament", "horse culture", "golden earth palette", "mobile settlement logic"],
    },
]

SCENES = [
    ("city_hall", "市政府", "civic administration and public square"),
    ("palace", "皇宫", "seat of rule or region-specific equivalent"),
    ("exchange", "证券交易所", "trade institution or region-specific equivalent"),
    ("university", "大学", "education institution or region-specific equivalent"),
    ("police", "警察局", "law-enforcement institution"),
    ("market", "闹市区", "commercial street and crowd density"),
    ("port", "码头", "waterfront, river crossing, or region-specific transport edge"),
    ("detached", "独栋别墅区", "detached affluent residential fabric"),
    ("townhouse", "联排别墅区", "attached residential fabric"),
    ("apartment", "公寓区", "dense residential fabric or region-specific equivalent"),
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _find_entry(archive: zipfile.ZipFile, suffix: str) -> zipfile.ZipInfo:
    matches = [entry for entry in archive.infolist() if entry.filename.replace("\\", "/").endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one ZIP member ending in {suffix!r}; found {len(matches)}")
    return matches[0]


def _save_visual(payload: bytes, destination: Path) -> dict:
    image = Image.open(io.BytesIO(payload)).convert("RGB")
    width, height = image.size
    crop = (
        round(width * CROP_NORM[0]),
        round(height * CROP_NORM[1]),
        round(width * CROP_NORM[2]),
        round(height * CROP_NORM[3]),
    )
    visual = image.crop(crop).resize(VISUAL_SIZE, Image.Resampling.NEAREST)
    visual = visual.quantize(colors=VISUAL_COLORS, method=Image.Quantize.MEDIANCUT).convert("RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    visual.save(destination, optimize=True)
    return {"source_size": [width, height], "crop_px": list(crop), "output_size": list(VISUAL_SIZE)}


def _save_review(payload: bytes, destination: Path) -> dict:
    image = Image.open(io.BytesIO(payload)).convert("RGB")
    width, height = image.size
    output_height = round(height * REVIEW_WIDTH / width)
    review = image.resize((REVIEW_WIDTH, output_height), Image.Resampling.NEAREST)
    review = review.quantize(colors=REVIEW_COLORS, method=Image.Quantize.MEDIANCUT).convert("RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    review.save(destination, optimize=True)
    return {"source_size": [width, height], "output_size": [REVIEW_WIDTH, output_height]}


def _load_ledger(review_zip: zipfile.ZipFile) -> tuple[bytes, dict[tuple[str, str], dict]]:
    entry = _find_entry(review_zip, "台账_registry.csv")
    payload = review_zip.read(entry)
    text = payload.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if len(rows) != 90:
        raise ValueError(f"review ledger must contain 90 rows; found {len(rows)}")
    return payload, {(row["国家"], row["场景"]): row for row in rows}


def import_scene_bible(source_dir: Path, output_root: Path) -> dict:
    review_zip_path = source_dir / "场景包_验收图与台账.zip"
    if not review_zip_path.exists():
        raise FileNotFoundError(review_zip_path)
    manifest = {
        "schema_version": 1,
        "scene_bible_version": "1.0.0",
        "role": "regional scene-level review bible",
        "authority_policy": {
            "level": "soft-reference",
            "authoritative_for": [
                "regional architectural language",
                "macro scene composition",
                "climate and vegetation cues",
                "material and color relationships",
                "scene-type differentiation",
            ],
            "soft_reference_for": ["accent colors", "prop motifs", "crowd and street density"],
            "not_authoritative_for": [
                "sprite dimensions",
                "character proportions",
                "paper-doll alignment",
                "animation motion or timing",
                "tile seams",
                "isolated asset silhouette",
                "HUD text or UI layout",
            ],
            "generation_rule": "Never use a Scene Bible image as the sole reference. Pair it with an approved category Gold Anchor.",
        },
        "visual_derivative": {
            "purpose": "HUD-free regional visual anchor",
            "crop_norm": list(CROP_NORM),
            "output_size": list(VISUAL_SIZE),
            "resample": "nearest",
            "color_limit": VISUAL_COLORS,
        },
        "regions": [],
        "scenes": [],
    }

    with zipfile.ZipFile(review_zip_path) as review_zip:
        ledger_payload, ledger = _load_ledger(review_zip)
        ledger_path = output_root / "source_registry.csv"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_bytes(ledger_payload)
        for region in REGIONS:
            review_entry = _find_entry(review_zip, f"验收_{region['name']}_10景.png")
            review_payload = review_zip.read(review_entry)
            review_destination = output_root / "review" / f"{region['slug']}.png"
            review_geometry = _save_review(review_payload, review_destination)
            manifest["regions"].append(
                {
                    "id": region["slug"],
                    "name": region["name"],
                    "visual_features": region["features"],
                    "review_image": review_destination.as_posix(),
                    "review_source": {
                        "package": review_zip_path.name,
                        "member": review_entry.filename,
                        "sha256": sha256_bytes(review_payload),
                    },
                    "review_geometry": review_geometry,
                }
            )

    for region in REGIONS:
        source_zip_path = source_dir / region["zip"]
        if not source_zip_path.exists():
            raise FileNotFoundError(source_zip_path)
        with zipfile.ZipFile(source_zip_path) as source_zip:
            for scene_slug, scene_name, scene_focus in SCENES:
                entry = _find_entry(source_zip, f"/{region['name']}/{scene_name}.png")
                payload = source_zip.read(entry)
                visual_destination = output_root / "visual" / region["slug"] / f"{scene_slug}.png"
                geometry = _save_visual(payload, visual_destination)
                review_row = ledger[(region["name"], scene_name)]
                manifest["scenes"].append(
                    {
                        "id": f"scene-{region['slug']}-{scene_slug}-v1",
                        "nation": {"id": region["slug"], "name": region["name"]},
                        "scene_type": {"id": scene_slug, "name": scene_name, "focus": scene_focus},
                        "visual_features": region["features"],
                        "adaptation_note": review_row["适配说明"] or None,
                        "supplied_review_status": review_row["验收"],
                        "authority": "soft-reference",
                        "visual_anchor": visual_destination.as_posix(),
                        "regional_review": f"assets/scene-bible/review/{region['slug']}.png",
                        "source": {
                            "package": source_zip_path.name,
                            "member": entry.filename,
                            "bytes": len(payload),
                            "sha256": sha256_bytes(payload),
                        },
                        "derivative": geometry,
                        "prohibited_uses": manifest["authority_policy"]["not_authoritative_for"],
                    }
                )

    if len(manifest["scenes"]) != 90:
        raise AssertionError(f"expected 90 scene records, generated {len(manifest['scenes'])}")
    manifest_path = output_root / "manifest.yaml"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Import and split the 90-scene regional review packages")
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("assets/scene-bible"),
    )
    args = parser.parse_args()
    manifest = import_scene_bible(args.source_dir, args.output_root)
    print(
        f"Imported {len(manifest['scenes'])} visual anchors and "
        f"{len(manifest['regions'])} review sheets into {args.output_root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
