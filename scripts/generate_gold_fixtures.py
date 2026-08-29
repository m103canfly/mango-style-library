#!/usr/bin/env python3
"""Generate small deterministic regression fixtures under tests/gold."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1] / "tests" / "gold"


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def paper_doll() -> None:
    base = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    draw.rectangle((27, 12, 36, 25), fill="#F2C49B")
    draw.rectangle((24, 26, 39, 67), fill="#2E3A54")
    draw.rectangle((24, 68, 30, 90), fill="#5A3826")
    draw.rectangle((33, 68, 39, 90), fill="#5A3826")
    save(base, ROOT / "shared_transform" / "base.png")

    outfit = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(outfit)
    draw.rectangle((22, 28, 41, 72), fill="#465672")
    draw.polygon([(22, 72), (41, 72), (44, 90), (19, 90)], fill="#2E3A54")
    save(outfit, ROOT / "shared_transform" / "outfit.png")

    hair = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hair)
    draw.rectangle((26, 9, 37, 17), fill="#3B2B24")
    draw.rectangle((25, 17, 38, 23), fill="#5A3826")
    save(hair, ROOT / "shared_transform" / "hair.png")


def motion() -> None:
    leg_phases = ((27, 38), (24, 38), (25, 40), (29, 36), (31, 42), (29, 39))
    for index, legs in enumerate(leg_phases):
        image = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((24, 10, 39, 27), fill="#F2C49B")
        draw.rectangle((20, 28, 43, 63), fill="#2E3A54")
        draw.rectangle((16, 34, 21, 58), fill="#465672")
        draw.rectangle((42, 34, 47, 58), fill="#465672")
        draw.line((29, 62, legs[0], 95), fill="#6B3E1D", width=8)
        draw.line((36, 62, legs[1], 95), fill="#8B5A2B", width=8)
        save(image, ROOT / "motion" / f"walk_{index}.png")


def palette() -> None:
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 3, 7), fill=(137, 79, 45, 255))
    draw.rectangle((4, 0, 7, 3), fill=(41, 104, 52, 255))
    draw.rectangle((4, 4, 7, 7), fill=(228, 177, 70, 255))
    save(image, ROOT / "palette" / "input.png")


def main() -> int:
    paper_doll()
    motion()
    palette()
    print(f"Generated regression fixtures in {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
