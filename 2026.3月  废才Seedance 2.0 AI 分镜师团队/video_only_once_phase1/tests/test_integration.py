from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from video_only_once_phase1.integration import build_bridge_commands
from video_only_once_phase1.workspace import prepare_runtime_dirs, resolve_workspace


class IntegrationTest(unittest.TestCase):
    def test_resolve_workspace_has_three_random_roots(self) -> None:
        rng = random.Random(404)
        for _ in range(3):
            suffix = rng.randint(100, 999)
            with tempfile.TemporaryDirectory(prefix=f"phase1-{suffix}-") as tmp:
                root = Path(tmp)
                (root / "video_only_once_phase1").mkdir()
                (root / "character_action").mkdir()
                (root / "fenjing_program").mkdir()
                (root / "zaomeng").mkdir()
                workspace = resolve_workspace(root)
                self.assertEqual(workspace.project_root, root.resolve())
                self.assertEqual(workspace.character_action_root.name, "character_action")
                self.assertEqual(workspace.fenjing_root.name, "fenjing_program")
                self.assertEqual(workspace.zaomeng_root.name, "zaomeng")

    def test_prepare_runtime_dirs_functional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "video_only_once_phase1").mkdir()
            (root / "character_action").mkdir()
            (root / "fenjing_program").mkdir()
            (root / "zaomeng").mkdir()
            workspace = resolve_workspace(root)
            created = prepare_runtime_dirs(workspace)
            self.assertEqual(len(created), 3)
            for path in created:
                self.assertTrue(path.exists())

    def test_build_bridge_commands_has_three_random_episode_cases(self) -> None:
        rng = random.Random(505)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "video_only_once_phase1").mkdir()
            (root / "character_action" / "configs").mkdir(parents=True)
            (root / "fenjing_program").mkdir()
            (root / "zaomeng" / "workflow" / "configs").mkdir(parents=True)
            workspace = resolve_workspace(root)
            for _ in range(3):
                episode = f"ep{rng.randint(1, 30):02d}"
                commands = build_bridge_commands(
                    workspace,
                    book_id="book-demo",
                    episode_id=episode,
                    browser="mock",
                    title="Demo Book",
                    language="en",
                    input_path="character_action/data/raw_books/demo.txt",
                )
                self.assertIn("character_action.cli", commands["character_action_prepare"])
                self.assertIn("preprocess-book", commands["character_action_preprocess"])
                self.assertIn("extract-characters", commands["character_action_extract"])
                self.assertIn("feicai_seedance.cli", commands["fenjing_status"])
                self.assertIn(episode, commands["fenjing_prompt"])
                self.assertIn("zaomeng_automation.cli", commands["zaomeng_run"])
                self.assertIn("extract-characters", commands["character_extract"])
                self.assertIn("export-character-reference-pack", commands["character_export_reference_pack"])
                self.assertIn("register-image", commands["register_image"])

    def test_cli_status_integration_uses_real_root_shape(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        project_root = package_root.parent
        command = [
            sys.executable,
            "-m",
            "video_only_once_phase1.cli",
            "status",
            "--project-root",
            str(project_root),
            "--episode",
            "ep01",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(package_root / "src")
        completed = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["character_action_exists"])
        self.assertTrue(payload["fenjing_exists"])
        self.assertTrue(payload["zaomeng_exists"])
        self.assertIn("phase2", payload)
        self.assertIn("character_action_configs_exists", payload["phase2"])
        self.assertIn("knowledge_base_exists", payload["phase2"])

    def test_cli_prepare_writes_phase2_episode_manifest(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "video_only_once_phase1").mkdir()
            (root / "character_action").mkdir()
            (root / "fenjing_program").mkdir()
            (root / "zaomeng").mkdir()
            command = [
                sys.executable,
                "-m",
                "video_only_once_phase1.cli",
                "prepare",
                "--project-root",
                str(root),
                "--book-id",
                "book-demo",
                "--episode",
                "ep03",
                "--browser",
                "mock",
            ]
            env = os.environ.copy()
            env["PYTHONPATH"] = str(package_root / "src")
            completed = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
            payload = json.loads(completed.stdout)
            manifest_path = Path(payload["phase2_manifest"])
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["task_id"], "phase02-ep03-character-anchor")
            self.assertEqual(manifest["character_system"]["root"], "character_action")
            self.assertEqual(manifest["image_generation"]["browser"], "mock")


if __name__ == "__main__":
    unittest.main()
