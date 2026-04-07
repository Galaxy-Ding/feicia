from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.asset_registry import load_asset_registry, sync_design_assets
from feicai_seedance.pipeline import Pipeline


class TestScenePipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        source_root = Path(__file__).resolve().parents[1]
        shutil.copy2(source_root / "project-config.json", self.root / "project-config.json")
        self.pipeline = Pipeline(self.root)

        character_content = (
            "# 人物提示词\n\n"
            "## 角色A（ep01 新增）\n\n"
            "**出图要求**：一张图\n\n"
            "**提示词**：角色A设定。\n"
        )
        scene_content = (
            "# 场景道具提示词\n\n"
            "## ep01 场景宫格\n\n"
            "### 视觉规范\n写实古风。\n\n"
            "### Panel Breakdown\n\n"
            "格1——【司天台】\n"
            "冷雾、高台、算筹。\n\n"
            "格2——【太史局内院】\n"
            "冷灰廊庑、将熄宫灯。\n\n"
            "格3——【空白占位】\n"
            "纯白留白。\n"
        )
        sync_design_assets(self.root, "ep01", character_content, scene_content)
        assets_dir = self.root / "assets"
        (assets_dir / "scene-prompts.md").write_text(
            "\n".join(
                [
                    "<!-- BEGIN SCENE:ep01 -->",
                    scene_content.strip(),
                    "<!-- END SCENE:ep01 -->",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_full_scene_asset_flow(self) -> None:
        self.pipeline.run_export_scene_image_tasks("ep01")
        self.pipeline.run_generate_scene_images("ep01", browser="mock")
        self.pipeline.run_review_scene_images("ep01")
        self.pipeline.run_approve_scene_assets("ep01")

        outputs_root = self.root / "outputs" / "ep01" / "scenes"
        self.assertTrue((outputs_root / "scene-image-tasks.json").exists())
        self.assertTrue((outputs_root / "scene-image-run.json").exists())
        self.assertTrue((outputs_root / "scene-review.json").exists())
        self.assertTrue((outputs_root / "scene-review.md").exists())
        self.assertTrue((outputs_root / "scene-asset-pack.json").exists())

        task_payload = json.loads((outputs_root / "scene-image-tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(task_payload["tasks"]), 2)
        self.assertEqual(len(task_payload["skipped_assets"]), 1)

        registry = load_asset_registry(self.root)
        ready_scenes = [item for item in registry["assets"] if item["asset_type"] == "scene_panel" and item["status"] == "READY_FOR_STORYBOARD"]
        self.assertEqual(len(ready_scenes), 2)
        self.assertTrue(all(item["image_path"].startswith("assets/library/scene-panels/") for item in ready_scenes))


if __name__ == "__main__":
    unittest.main()
