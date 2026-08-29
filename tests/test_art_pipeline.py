from __future__ import annotations

import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from godot_export import process_group  # noqa: E402
from art_score import score_review  # noqa: E402
from motion_audit import audit_frames  # noqa: E402
from package_asset import package_asset as package_native_asset  # noqa: E402
from palette_remap import build_palette, load_palette_config, remap_image  # noqa: E402
from tingen_contract import DEFAULT_PROFILE, audit_native_png, load_json, resolve_asset_contract  # noqa: E402
from validate_anchor_pack import validate as validate_anchor_pack  # noqa: E402
from validate_delivery import validate_delivery  # noqa: E402
from validate_project_profile import validate as validate_project_profile  # noqa: E402


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
            self.assertEqual(metadata["transform"]["baseline"], 95)
            self.assertEqual(metadata["transform"]["runtime_anchor"], [32, 96])
            self.assertEqual(metadata["transform"]["anchor_coordinate_kind"], "canvas_boundary")
            self.assertEqual(metadata["transform"]["source_canvas"], [64, 96])
            self.assertEqual(metadata["lifecycle_status"], "reference_candidate_not_runtime_ready")
            self.assertFalse(metadata["delivery_eligible"])
            self.assertTrue(metadata["transform_id"].startswith("transform-"))
            self.assertTrue((Path(temporary) / "layer" / "paper_doll_test.transform.json").is_file())
            sizes = []
            boxes = []
            for path in outputs:
                with Image.open(path) as image:
                    sizes.append(image.size)
                    boxes.append(image.getchannel("A").getbbox())
            self.assertTrue(all(size == (64, 96) for size in sizes))
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
            for index in range(6)
        ]
        result = audit_frames(frames, animation_type="walk")
        self.assertEqual(result["verdict"], "APPROVE", result)
        self.assertLessEqual(result["metrics"]["foot_baseline_drift_px"], 1)
        self.assertEqual(result["expected_foot_anchor"], [32, 96])

    def test_baseline_drift_is_rejected(self) -> None:
        source = Image.open(ROOT / "tests" / "gold" / "motion" / "walk_0.png").convert("RGBA")
        shifted = Image.new("RGBA", source.size, (0, 0, 0, 0))
        shifted.alpha_composite(source, (0, -4))
        frames = [source] * 5 + [shifted]
        result = audit_frames(frames, animation_type="walk")
        self.assertEqual(result["verdict"], "REJECT", result)
        self.assertIn("foot_anchor_y", result["reject_failures"])


class TingenDeliveryTests(unittest.TestCase):
    def test_native_character_is_packaged_without_resizing_runtime_png(self) -> None:
        source = ROOT / "tests" / "gold" / "motion" / "walk_0.png"
        with tempfile.TemporaryDirectory() as temporary:
            args = Namespace(
                input=source,
                output_root=Path(temporary),
                profile=DEFAULT_PROFILE,
                asset_id="character.test.walk.south.001.v001",
                asset_name="test_walk_south_01",
                asset_class="character_frame",
                district_id="tingen.district.golden_indus",
                facing="south",
                material_id=["skin.fair", "cloth.navy", "wood.warm"],
                source_status="pixel_redraw_from_generated_reference",
                reference_id=["character_gold_test"],
                task_contract=None,
                review_json=None,
                lifecycle_status="candidate_pending_user_1x_review",
            )
            directory = package_native_asset(args)
            result = validate_delivery(directory)
            self.assertTrue(result["valid"], result)
            self.assertFalse(result["runtime_ready"])
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["dimensions"], [64, 96])
            self.assertEqual(manifest["anchor"], [32, 96])
            with Image.open(directory / "test_walk_south_01_1x.png") as one_x:
                self.assertEqual(one_x.size, (64, 96))
            with Image.open(directory / "test_walk_south_01_4x.png") as four_x:
                self.assertEqual(four_x.size, (256, 384))

    def test_semitransparent_alpha_is_rejected(self) -> None:
        profile = load_json(DEFAULT_PROFILE)
        contract = resolve_asset_contract(profile, "character_frame")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad_alpha.png"
            image = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
            image.putpixel((32, 95), (242, 196, 155, 128))
            image.save(path)
            result = audit_native_png(path, profile, DEFAULT_PROFILE, contract, ["skin.fair"])
            self.assertEqual(result["verdict"], "REJECT", result)
            self.assertTrue(any("alpha values" in error for error in result["errors"]))


class ArtScoreTests(unittest.TestCase):
    @staticmethod
    def perfect_payload() -> dict:
        dimensions = {
            name: {"grade": 5, "evidence": [f"audit.json#{name}"]}
            for name in (
                "technical_integrity", "silhouette_composition", "style_palette",
                "category_regional_identity", "scale_alignment", "motion_continuity",
            )
        }
        return {
            "asset_id": "character.test.v001",
            "profile_id": "tingen_pixel_v3_hd",
            "reviewer": "test-reviewer",
            "reviewed_at": "2026-08-29T12:00:00+08:00",
            "critical_failures": [],
            "dimensions": dimensions,
        }

    def test_evidenced_perfect_review_is_approve(self) -> None:
        result = score_review(self.perfect_payload())
        self.assertEqual(result["review_score"], 100)
        self.assertEqual(result["review_verdict"], "APPROVE")
        self.assertTrue(result["gold_anchor_eligible"])

    def test_critical_failure_overrides_perfect_score(self) -> None:
        payload = self.perfect_payload()
        payload["critical_failures"] = ["generated_hd_reference_direct_delivery"]
        result = score_review(payload)
        self.assertEqual(result["review_score"], 100)
        self.assertEqual(result["review_verdict"], "REJECT")
        self.assertFalse(result["gold_anchor_eligible"])


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

    def test_project_profile_is_valid_but_release_blockers_are_honest(self) -> None:
        result = validate_project_profile(DEFAULT_PROFILE, ROOT)
        self.assertTrue(result["valid"], result)
        self.assertFalse(result["release_ready"])
        self.assertIn("Tingen RGB palette is provisional and has not been project-approved", result["blockers"])
        self.assertIn("Category Gold Anchor Pack is not release-ready", result["blockers"])


if __name__ == "__main__":
    unittest.main()
