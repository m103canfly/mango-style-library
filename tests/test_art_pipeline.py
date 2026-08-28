from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from godot_export import process_group  # noqa: E402
from motion_audit import audit_frames  # noqa: E402
from palette_remap import build_palette, load_palette_config, remap_image  # noqa: E402
from validate_anchor_pack import validate as validate_anchor_pack  # noqa: E402


class SharedTransformTests(unittest.TestCase):
    def test_paper_doll_group_uses_one_transform_and_baseline(self) -> None:
        fixtures = ROOT / "tests" / "gold" / "shared_transform"
        inputs = [fixtures / "base.png", fixtures / "outfit.png", fixtures / "hair.png"]
        with tempfile.TemporaryDirectory() as temporary:
            outputs, metadata = process_group(
                inputs,
                "layer",
                temporary,
                group_id="paper_doll_test",
                use_palette=False,
                remove_watermark=False,
                resample="nearest",
            )
            self.assertEqual(metadata["member_count"], 3)
            self.assertEqual(metadata["transform"]["baseline"], 47)
            self.assertEqual(metadata["transform"]["source_canvas"], [64, 96])
            self.assertTrue(metadata["transform_id"].startswith("transform-"))
            self.assertTrue((Path(temporary) / "layer" / "paper_doll_test.transform.json").is_file())
            sizes = []
            boxes = []
            for path in outputs:
                with Image.open(path) as image:
                    sizes.append(image.size)
                    boxes.append(image.getchannel("A").getbbox())
            self.assertTrue(all(size == (32, 48) for size in sizes))
            base_bbox, outfit_bbox = boxes[:2]
            self.assertEqual(base_bbox[3], outfit_bbox[3])


class PaletteTests(unittest.TestCase):
    def test_remap_output_is_subset_of_declared_palette(self) -> None:
        config = load_palette_config(ROOT / "assets" / "palettes" / "palettes.json")
        palette, metadata = build_palette(config, region="loen", specials=("ui",))
        image = Image.open(ROOT / "tests" / "gold" / "palette" / "input.png")
        output = remap_image(image, palette)
        rgb = np.asarray(output)[..., :3]
        alpha = np.asarray(output)[..., 3]
        actual = {tuple(color) for color in rgb[alpha > 0]}
        declared = {tuple(color) for color in palette}
        self.assertTrue(actual <= declared)
        self.assertIn("mango-master-v1", metadata["palette_ids"])
        self.assertIn("region-loen-v1", metadata["palette_ids"])


class MotionTests(unittest.TestCase):
    def test_gold_walk_passes_motion_audit(self) -> None:
        frames = [
            Image.open(ROOT / "tests" / "gold" / "motion" / f"walk_{index}.png").convert("RGBA")
            for index in range(3)
        ]
        result = audit_frames(frames)
        self.assertEqual(result["verdict"], "APPROVE", result)
        self.assertLessEqual(result["metrics"]["foot_baseline_drift_px"], 1)

    def test_baseline_drift_is_rejected(self) -> None:
        source = Image.open(ROOT / "tests" / "gold" / "motion" / "walk_0.png").convert("RGBA")
        shifted = Image.new("RGBA", source.size, (0, 0, 0, 0))
        shifted.alpha_composite(source, (0, -4))
        result = audit_frames([source, shifted])
        self.assertEqual(result["verdict"], "REJECT", result)
        self.assertIn("foot_baseline_drift_px", result["reject_failures"])


class SceneBibleTests(unittest.TestCase):
    def test_scene_bible_has_90_unique_soft_references(self) -> None:
        manifest_path = ROOT / "assets" / "scene-bible" / "manifest.yaml"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["regions"]), 9)
        self.assertEqual(len(manifest["scenes"]), 90)
        ids = [scene["id"] for scene in manifest["scenes"]]
        self.assertEqual(len(ids), len(set(ids)))
        for scene in manifest["scenes"]:
            self.assertEqual(scene["authority"], "soft-reference")
            self.assertTrue((ROOT / scene["visual_anchor"]).is_file())
            self.assertEqual(len(scene["source"]["sha256"]), 64)
            self.assertIn("animation motion or timing", scene["prohibited_uses"])


class AnchorPackTests(unittest.TestCase):
    def test_anchor_manifest_is_valid_but_not_falsely_release_ready(self) -> None:
        result = validate_anchor_pack(
            ROOT / "assets" / "anchors" / "style-anchor-manifest.yaml",
            ROOT,
        )
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["release_ready"])
        self.assertEqual(result["approved_anchor_count"], 0)


if __name__ == "__main__":
    unittest.main()
