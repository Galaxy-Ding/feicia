from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.asset_registry import build_reference_map, register_asset_image, sync_design_assets
from feicai_seedance.structured_protocols import ensure_asset_registry_files


class TestAssetRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        ensure_asset_registry_files(self.root / "assets")
        output_dir = self.root / "outputs" / "ep01"
        output_dir.mkdir(parents=True, exist_ok=True)
        director_payload = {
            "episode": "ep01",
            "plot_points": [
                {
                    "id": "P01",
                    "title": "开场",
                    "characters": ["角色A"],
                    "scenes": ["旧屋客厅"],
                    "shot_group_type": "single_shot",
                    "duration_seconds": 8,
                    "beats": [],
                    "safe_zone": {"head_seconds": 0.5, "tail_seconds": 0.5},
                    "narration": "角色A推门进入，镜头缓慢推近，冷白台灯照着桌面。",
                }
            ],
            "characters": [{"人物": "角色A"}],
            "scenes": [{"场景": "旧屋客厅"}],
            "rule_flags": [],
        }
        (output_dir / "01-director-analysis.json").write_text(json.dumps(director_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sync_design_assets_three_random_cases(self) -> None:
        for index in range(3):
            scene_name = f"旧屋客厅{index}"
            character_content = (
                "# 人物提示词\n\n"
                "## 角色A（ep01 新增）\n\n"
                "**出图要求**：一张图\n\n"
                f"**提示词**：角色A设定{random.randint(1, 999)}。\n"
            )
            scene_content = (
                "# 场景道具提示词\n\n"
                "## ep01 场景宫格\n\n"
                "请生成一张 3x3 宫格布局的电影场景环境图像。\n\n"
                "### 视觉规范\n写实\n\n"
                "### Panel Breakdown\n\n"
                f"格1——【{scene_name}】\n"
            )
            with self.subTest(index=index):
                result = sync_design_assets(self.root, "ep01", character_content, scene_content)
                self.assertGreaterEqual(len(result["character_assets"]), 1)
                self.assertGreaterEqual(len(result["scene_assets"]), 2)

    def test_register_asset_image_and_build_reference_map(self) -> None:
        character_content = (
            "# 人物提示词\n\n"
            "## 角色A（ep01 新增）\n\n"
            "**出图要求**：一张图\n\n"
            "**提示词**：角色A设定。\n"
        )
        scene_content = (
            "# 场景道具提示词\n\n"
            "## ep01 场景宫格\n\n"
            "请生成一张 3x3 宫格布局的电影场景环境图像。\n\n"
            "### 视觉规范\n写实\n\n"
            "### Panel Breakdown\n\n"
            "格1——【旧屋客厅】\n"
        )
        sync_result = sync_design_assets(self.root, "ep01", character_content, scene_content)
        image_dir = self.root / "tmp-images"
        image_dir.mkdir(parents=True, exist_ok=True)
        image_file = image_dir / "ref.png"
        image_file.write_bytes(b"fakepng")

        character_id = next(item["asset_id"] for item in sync_result["character_assets"] if item["asset_type"] == "character")
        panel_id = next(item["asset_id"] for item in sync_result["scene_assets"] if item["asset_type"] == "scene_panel")
        register_asset_image(self.root, character_id, str(image_file))
        register_asset_image(self.root, panel_id, str(image_file))

        reference_map = build_reference_map(self.root, "ep01")
        self.assertEqual(len(reference_map["references"]), 2)
        self.assertEqual(reference_map["missing_assets"], [])


if __name__ == "__main__":
    unittest.main()
