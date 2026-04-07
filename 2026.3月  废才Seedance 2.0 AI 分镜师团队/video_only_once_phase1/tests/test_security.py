from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from video_only_once_phase1.integration import build_zaomeng_run_command
from video_only_once_phase1.workspace import ensure_within_root, resolve_workspace


class SecurityTest(unittest.TestCase):
    def test_ensure_within_root_rejects_three_random_escape_cases(self) -> None:
        rng = random.Random(606)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            safe_child = root / "child"
            safe_child.mkdir()
            for _ in range(3):
                escape_depth = rng.randint(1, 4)
                target = root.joinpath(*([".."] * escape_depth), "escape")
                with self.assertRaises(ValueError):
                    ensure_within_root(root, target)

    def test_invalid_browser_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "video_only_once_phase1").mkdir()
            (root / "character_action").mkdir()
            (root / "fenjing_program").mkdir()
            (root / "zaomeng").mkdir()
            workspace = resolve_workspace(root)
            for browser in ["chrome", "unsafe", ""]:
                with self.assertRaises(ValueError):
                    build_zaomeng_run_command(workspace, browser)

    def test_safe_path_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "safe" / "file.txt"
            nested.parent.mkdir(parents=True)
            nested.touch()
            self.assertEqual(ensure_within_root(root, nested), nested.resolve())


if __name__ == "__main__":
    unittest.main()
