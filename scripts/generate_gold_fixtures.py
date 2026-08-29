#!/usr/bin/env python3
"""Generate small deterministic regression fixtures under tests/gold."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "tests" / "gold"
MATERIALS = json.loads(
    (PROJECT_ROOT / "assets" / "palettes" / "tingen-materials.json").read_text(encoding="utf-8")
)["materials"]
MASTER_COLORS = json.loads(
    (PROJECT_ROOT / "assets" / "palettes" / "tingen-template-palette.json").read_text(encoding="utf-8")
)["master"]["colors"]


def ramp(material_id: str) -> list[str]:
    return [entry["color"] for entry in MATERIALS[material_id]["tone_ramp"]]


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def paper_doll() -> None:
    skin, cloth, wood = ramp("skin.fair"), ramp("cloth.navy"), ramp("wood.warm")
    base = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    draw.rectangle((27, 12, 36, 25), fill=skin[1])
    draw.rectangle((24, 26, 39, 67), fill=cloth[2])
    draw.rectangle((24, 68, 30, 90), fill=wood[1])
    draw.rectangle((33, 68, 39, 90), fill=wood[2])
    save(base, ROOT / "shared_transform" / "base.png")

    outfit = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(outfit)
    draw.rectangle((22, 28, 41, 72), fill=cloth[3])
    draw.polygon([(22, 72), (41, 72), (44, 90), (19, 90)], fill=cloth[1])
    save(outfit, ROOT / "shared_transform" / "outfit.png")

    hair = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hair)
    draw.rectangle((26, 9, 37, 17), fill=wood[0])
    draw.rectangle((25, 17, 38, 23), fill=wood[2])
    save(hair, ROOT / "shared_transform" / "hair.png")


def motion() -> None:
    skin, cloth, wood = ramp("skin.fair"), ramp("cloth.navy"), ramp("wood.warm")
    leg_phases = ((27, 38), (24, 38), (25, 40), (29, 36), (31, 42), (29, 39))
    for index, legs in enumerate(leg_phases):
        image = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((24, 10, 39, 27), fill=skin[1])
        draw.rectangle((20, 28, 43, 63), fill=cloth[2])
        draw.rectangle((16, 34, 21, 58), fill=cloth[1])
        draw.rectangle((42, 34, 47, 58), fill=cloth[3])
        draw.line((29, 62, legs[0], 95), fill=wood[1], width=8)
        draw.line((36, 62, legs[1], 95), fill=wood[2], width=8)
        save(image, ROOT / "motion" / f"walk_{index}.png")


def palette() -> None:
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 3, 7), fill=MASTER_COLORS[31])
    draw.rectangle((4, 0, 7, 3), fill=MASTER_COLORS[52])
    draw.rectangle((4, 4, 7, 7), fill=MASTER_COLORS[42])
    save(image, ROOT / "palette" / "input.png")


def main() -> int:
    paper_doll()
    motion()
    palette()
    print(f"Generated regression fixtures in {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
