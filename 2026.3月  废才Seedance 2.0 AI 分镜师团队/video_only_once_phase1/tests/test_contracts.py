from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from video_only_once_phase1.contracts import (
    build_episode_task,
    build_phase2_episode_manifest,
    build_task_id,
    decide_gate,
    normalize_episode_id,
)
from video_only_once_phase1.workspace import resolve_workspace


class ContractsTest(unittest.TestCase):
    def test_normalize_episode_id_has_three_random_cases(self) -> None:
        rng = random.Random(101)
        for _ in range(3):
            number = rng.randint(1, 999)
            self.assertEqual(normalize_episode_id(str(number)), f"ep{number:0{max(2, len(str(number)))}d}")

    def test_build_task_id_has_three_random_cases(self) -> None:
        rng = random.Random(202)
        for _ in range(3):
            number = rng.randint(1, 88)
            task_id = build_task_id("phase01", f"ep{number}", "integration")
            self.assertEqual(task_id, f"phase01-ep{number:02d}-integration")

    def test_build_episode_task_has_three_random_cases(self) -> None:
        rng = random.Random(303)
        for _ in range(3):
            number = rng.randint(1, 50)
            task = build_episode_task("book-demo", str(number), upstream=["director"])
            self.assertEqual(task["episode_id"], f"ep{number:02d}")
            self.assertEqual(task["manual_checkpoints"], 1)
            self.assertEqual(task["upstream"], ["director"])

    def test_decide_gate_has_three_random_cases(self) -> None:
        cases = [
            {"passed": True, "manual_required": False, "retryable": False, "expected": "AUTO_CONTINUE"},
            {"passed": False, "manual_required": True, "retryable": True, "expected": "MANUAL_REVIEW"},
            {"passed": False, "manual_required": False, "retryable": True, "expected": "RETRY"},
        ]
        for index, case in enumerate(cases, start=1):
            gate = decide_gate(
                f"ep0{index}",
                "integration",
                passed=case["passed"],
                manual_required=case["manual_required"],
                retryable=case["retryable"],
                reason_codes=["CASE"],
            )
            self.assertEqual(gate["decision"], case["expected"])

    def test_build_phase2_episode_manifest_has_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "video_only_once_phase1").mkdir()
            (root / "character_action").mkdir()
            (root / "fenjing_program").mkdir()
            (root / "zaomeng").mkdir()
            workspace = resolve_workspace(root)
            manifest = build_phase2_episode_manifest(workspace, "book-demo", "1", browser="mock")
            self.assertEqual(manifest["phase"], "phase02")
            self.assertEqual(manifest["stage"], "character_anchor")
            self.assertEqual(manifest["episode_id"], "ep01")
            self.assertEqual(manifest["upstream"], ["phase01-ep01-integration"])
            self.assertEqual(manifest["character_system"]["root"], "character_action")
            self.assertEqual(manifest["character_system"]["book_outputs"]["character_cards"], "character_action/data/exports/book_demo/character_cards.json")
            self.assertEqual(manifest["knowledge_base"]["entities"]["characters"], "fenjing_program/project_data/knowledge_base/entities/characters.json")
            self.assertEqual(manifest["character_anchor"]["outputs"]["character_image_tasks"], "fenjing_program/outputs/ep01/characters/character-image-tasks.json")
            self.assertEqual(manifest["image_generation"]["images_root"], "zaomeng/downloads/images/characters/ep01")
            self.assertEqual(manifest["registry_writeback"]["asset_registry"], "fenjing_program/assets/registry/asset-registry.json")

    def test_invalid_episode_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_episode_id("episode-one")


if __name__ == "__main__":
    unittest.main()
