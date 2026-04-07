from __future__ import annotations

import random
import shutil
import tempfile
import unittest
import json
from pathlib import Path

from feicai_seedance.acceptance_store import save_stage_acceptance
from feicai_seedance.artifact_utils import upsert_episode_block
from feicai_seedance.config import ensure_runtime_directories, load_config
from feicai_seedance.status import detect_all_statuses, detect_episode_status, pick_default_episode
from feicai_seedance.structured_protocols import ensure_asset_registry_files


class TestStatus(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        source_root = Path(__file__).resolve().parents[1]
        prompt_assets_root = source_root if (source_root / "agents").exists() else source_root.parent / "0-origin_document"
        for name in ["agents", "skills", "CLAUDE.md"]:
            src = prompt_assets_root / name
            dst = self.root / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        shutil.copy2(source_root / "project-config.json", self.root / "project-config.json")
        self.config = load_config(self.root)
        ensure_runtime_directories(self.config)
        ensure_asset_registry_files(self.config.paths.assets)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_detect_episode_status_randomized(self) -> None:
        for index in range(3):
            episode = f"ep{index + 1:02d}"
            script = self.config.paths.scripts / f"{episode}-sample.md"
            script.write_text(f"剧本 {random.randint(1, 999)}", encoding="utf-8")
            status = detect_episode_status(self.config, episode, script)
            self.assertEqual(status.stage, "DIRECTOR_ANALYSIS")

    def test_pick_default_episode(self) -> None:
        for episode in ["ep01", "ep02", "ep03"]:
            (self.config.paths.scripts / f"{episode}-sample.md").write_text("content", encoding="utf-8")
        statuses = detect_all_statuses(self.config)
        self.assertEqual(pick_default_episode(statuses), "ep01")

    def test_done_status(self) -> None:
        episode = "ep01"
        (self.config.paths.scripts / f"{episode}-sample.md").write_text("content", encoding="utf-8")
        output_dir = self.config.paths.outputs / episode
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "01-director-analysis.md").write_text("a", encoding="utf-8")
        (output_dir / "02-seedance-prompts.md").write_text("b", encoding="utf-8")
        upsert_episode_block(self.config.paths.assets / "character-prompts.md", episode, "CHARACTER", "c")
        upsert_episode_block(self.config.paths.assets / "scene-prompts.md", episode, "SCENE", "d")
        save_stage_acceptance(self.config.paths.reports, episode, "director", "accepted", "manual")
        save_stage_acceptance(self.config.paths.reports, episode, "design", "accepted", "manual")
        save_stage_acceptance(self.config.paths.reports, episode, "prompt", "accepted", "manual")
        registry_payload = {
            "version": "1.0",
            "updated_at": "2026-03-25T10:00:00+08:00",
            "assets": [
                {"asset_id": "char-1", "asset_type": "character", "name": "c", "episode_origin": episode, "status": "READY_FOR_STORYBOARD"},
                {"asset_id": "scene-1", "asset_type": "scene_panel", "name": "d", "episode_origin": episode, "status": "READY_FOR_STORYBOARD"},
            ],
        }
        (self.config.paths.assets / "registry" / "asset-registry.json").write_text(json.dumps(registry_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "reference-map.json").write_text(
            json.dumps({"episode": episode, "references": [{"ref_id": "@图片1"}], "missing_assets": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        status = detect_episode_status(self.config, episode, self.config.paths.scripts / f"{episode}-sample.md")
        self.assertEqual(status.stage, "DONE")

    def test_image_pending_status(self) -> None:
        episode = "ep01"
        (self.config.paths.scripts / f"{episode}-sample.md").write_text("content", encoding="utf-8")
        output_dir = self.config.paths.outputs / episode
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "01-director-analysis.md").write_text("a", encoding="utf-8")
        upsert_episode_block(self.config.paths.assets / "character-prompts.md", episode, "CHARACTER", "c")
        upsert_episode_block(self.config.paths.assets / "scene-prompts.md", episode, "SCENE", "d")
        save_stage_acceptance(self.config.paths.reports, episode, "director", "accepted", "manual")
        save_stage_acceptance(self.config.paths.reports, episode, "design", "accepted", "manual")
        status = detect_episode_status(self.config, episode, self.config.paths.scripts / f"{episode}-sample.md")
        self.assertEqual(status.stage, "IMAGE_PENDING")

    def test_reference_mapping_pending_status(self) -> None:
        episode = "ep01"
        (self.config.paths.scripts / f"{episode}-sample.md").write_text("content", encoding="utf-8")
        output_dir = self.config.paths.outputs / episode
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "01-director-analysis.md").write_text("a", encoding="utf-8")
        upsert_episode_block(self.config.paths.assets / "character-prompts.md", episode, "CHARACTER", "c")
        upsert_episode_block(self.config.paths.assets / "scene-prompts.md", episode, "SCENE", "d")
        save_stage_acceptance(self.config.paths.reports, episode, "director", "accepted", "manual")
        save_stage_acceptance(self.config.paths.reports, episode, "design", "accepted", "manual")
        registry_payload = {
            "version": "1.0",
            "updated_at": "2026-03-25T10:00:00+08:00",
            "assets": [
                {"asset_id": "char-1", "asset_type": "character", "name": "c", "episode_origin": episode, "status": "READY_FOR_STORYBOARD"},
                {"asset_id": "scene-1", "asset_type": "scene_panel", "name": "d", "episode_origin": episode, "status": "READY_FOR_STORYBOARD"},
            ],
        }
        (self.config.paths.assets / "registry" / "asset-registry.json").write_text(json.dumps(registry_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        status = detect_episode_status(self.config, episode, self.config.paths.scripts / f"{episode}-sample.md")
        self.assertEqual(status.stage, "REFERENCE_MAPPING_PENDING")


if __name__ == "__main__":
    unittest.main()
