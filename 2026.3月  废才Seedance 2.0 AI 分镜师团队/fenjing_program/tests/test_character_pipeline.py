from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.asset_registry import load_asset_registry
from feicai_seedance.pipeline import Pipeline


class TestCharacterPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        source_root = Path(__file__).resolve().parents[1]
        shutil.copy2(source_root / "project-config.json", self.root / "project-config.json")
        (self.root / "script").mkdir(parents=True, exist_ok=True)
        (self.root / "script" / "ep01-demo.md").write_text(
            "# ep01\n\n林书白在破屋里翻书，随后抬头看向窗外。林书白听见风声，继续握紧旧剑。\n",
            encoding="utf-8",
        )
        self.pipeline = Pipeline(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_full_character_anchor_flow(self) -> None:
        self.pipeline.run_extract_characters("book-demo", "ep01")
        self.pipeline.run_build_character_sheets("book-demo", "ep01")
        self.pipeline.run_export_character_image_tasks("book-demo", "ep01")
        self.pipeline.run_generate_character_images("book-demo", "ep01", browser="mock")
        self.pipeline.run_review_character_images("book-demo", "ep01")
        self.pipeline.run_approve_character_assets("book-demo", "ep01")
        self.pipeline.run_export_character_reference_pack("book-demo", "ep01")

        outputs_root = self.root / "outputs" / "ep01" / "characters"
        self.assertTrue((outputs_root / "character-candidate-list.json").exists())
        self.assertTrue((outputs_root / "character-sheets.json").exists())
        self.assertTrue((outputs_root / "character-sheets.md").exists())
        self.assertTrue((outputs_root / "character-image-tasks.json").exists())
        self.assertTrue((outputs_root / "character-image-run.json").exists())
        self.assertTrue((outputs_root / "character-review.json").exists())
        self.assertTrue((outputs_root / "character-review.md").exists())
        self.assertTrue((outputs_root / "character-anchor-pack.json").exists())
        self.assertTrue((outputs_root / "character-reference-pack.json").exists())

        review_payload = json.loads((outputs_root / "character-review.json").read_text(encoding="utf-8"))
        self.assertEqual(review_payload["characters"][0]["overall_status"], "passed")
        self.assertTrue(review_payload["characters"][0]["ready_for_anchor"])

        reference_payload = json.loads((outputs_root / "character-reference-pack.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(reference_payload["characters"]), 1)
        self.assertTrue(reference_payload["characters"][0]["primary_image"].startswith("assets/library/characters/"))

        registry = load_asset_registry(self.root)
        character_asset = next(item for item in registry["assets"] if item["asset_type"] == "character")
        self.assertEqual(character_asset["status"], "READY_FOR_STORYBOARD")
        self.assertIn("front_full_body", character_asset["reference_images"])

    def test_help_lists_character_commands(self) -> None:
        help_text = self.pipeline.command_help()
        self.assertIn("extract-characters <book_id> <ep01>", help_text)
        self.assertIn("approve-character-assets <book_id> <ep01>", help_text)
        self.assertIn("export-scene-image-tasks <ep01>", help_text)

    def test_extract_characters_prefers_design_character_headings(self) -> None:
        outputs_root = self.root / "outputs" / "ep01"
        outputs_root.mkdir(parents=True, exist_ok=True)
        (outputs_root / "01-director-analysis.json").write_text(
            json.dumps(
                {
                    "episode": "ep01",
                    "plot_points": [
                        {"id": "P01", "characters": ["顾星澜", "太史局同僚"], "scenes": ["司天台"]},
                        {"id": "P02", "characters": ["顾星澜", "守门内侍"], "scenes": ["书房门外"]},
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        assets_dir = self.root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "character-prompts.md").write_text(
            "\n".join(
                [
                    "<!-- BEGIN CHARACTER:ep01 -->",
                    "# 人物提示词",
                    "",
                    "## 顾星澜（ep01 新增）",
                    "",
                    "## 守门内侍（ep01 新增）",
                    "",
                    "<!-- END CHARACTER:ep01 -->",
                ]
            ),
            encoding="utf-8",
        )
        (self.root / "script" / "ep01-demo.md").write_text(
            "开元十六年，朝廷以陕甘大旱为由减免税银三十七万两。算天象者，当知天时不可违，但人事可为。",
            encoding="utf-8",
        )

        self.pipeline.run_extract_characters("book-demo", "ep01")

        payload = json.loads((outputs_root / "characters" / "character-candidate-list.json").read_text(encoding="utf-8"))
        self.assertEqual([item["name"] for item in payload["characters"]], ["顾星澜", "守门内侍", "太史局同僚"])


if __name__ == "__main__":
    unittest.main()
