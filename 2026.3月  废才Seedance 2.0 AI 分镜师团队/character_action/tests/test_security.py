from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from character_action.config import ensure_within_root, load_config
from character_action.ids import normalize_book_id


class SecurityTest(unittest.TestCase):
    def test_ensure_within_root_rejects_three_random_escape_cases(self) -> None:
        rng = random.Random(1501)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for _ in range(3):
                escape_depth = rng.randint(1, 3)
                target = root.joinpath(*([".."] * escape_depth), "escape.txt")
                with self.assertRaises(ValueError):
                    ensure_within_root(root, target)

    def test_load_config_rejects_invalid_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "configs").mkdir()
            (root / "configs" / "dev.yaml").write_text(
                "project_root: .\n"
                "data:\n"
                "  raw_books: data/raw_books\n"
                "  normalized: data/normalized\n"
                "  exports: data/exports\n"
                "  logs: logs\n"
                "runtime:\n"
                "  sqlite_path: data/exports/character_action.sqlite3\n"
                "  chunk_size: 40\n"
                "  chunk_overlap: 40\n"
                "  evidence_window: 8\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_config(root)

    def test_load_config_rejects_invalid_adapter_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "configs").mkdir()
            (root / "configs" / "dev.yaml").write_text(
                "project_root: .\n"
                "data:\n"
                "  raw_books: data/raw_books\n"
                "  normalized: data/normalized\n"
                "  exports: data/exports\n"
                "  logs: logs\n"
                "runtime:\n"
                "  sqlite_path: data/exports/character_action.sqlite3\n"
                "  chunk_size: 40\n"
                "  chunk_overlap: 10\n"
                "  evidence_window: 8\n"
                "  adapter_mode: unsafe\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_config(root)

    def test_normalize_book_id_has_three_random_safe_cases(self) -> None:
        rng = random.Random(1502)
        for _ in range(3):
            suffix = rng.randint(1, 999)
            self.assertTrue(normalize_book_id(f"Demo {suffix}").startswith("book_demo_"))


if __name__ == "__main__":
    unittest.main()
