from __future__ import annotations

import random
import string
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.utils import (
    choose_grid_spec,
    extract_episode_id,
    extract_json_object,
    safe_relative_path,
    sanitize_episode_id,
)


class TestUtils(unittest.TestCase):
    def test_extract_episode_id_with_random_cases(self) -> None:
        for index in range(3):
            suffix = "".join(random.choices(string.ascii_lowercase, k=5))
            filename = f"{random.choice(['EP', 'ep'])}{index + 1:02d}-{suffix}.md"
            with self.subTest(filename=filename):
                self.assertEqual(extract_episode_id(filename), f"ep{index + 1:02d}")

    def test_sanitize_episode_id_with_random_cases(self) -> None:
        for _ in range(3):
            number = random.randint(1, 9)
            raw = f" EP{number:02d} "
            with self.subTest(raw=raw):
                self.assertEqual(sanitize_episode_id(raw), f"ep{number:02d}")

    def test_choose_grid_spec_with_random_cases(self) -> None:
        cases = [(random.randint(1, 9), "3x3"), (random.randint(10, 12), "3x4"), (random.randint(13, 16), "4x4")]
        for scene_count, expected in cases:
            with self.subTest(scene_count=scene_count):
                self.assertEqual(choose_grid_spec(scene_count), expected)

    def test_extract_json_object(self) -> None:
        for payload in ['prefix {"result":"PASS"} suffix', '\n{"issues":[]}\n', '{"value":1}']:
            with self.subTest(payload=payload):
                self.assertIsInstance(extract_json_object(payload), dict)

    def test_safe_relative_path_security(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for suffix in ["a.txt", "nested/b.txt", "nested/deep/c.txt"]:
                with self.subTest(suffix=suffix):
                    target = safe_relative_path(root, suffix)
                    self.assertTrue(str(target).startswith(str(root.resolve())))
            with self.assertRaises(ValueError):
                safe_relative_path(root, "../escape.txt")


if __name__ == "__main__":
    unittest.main()
