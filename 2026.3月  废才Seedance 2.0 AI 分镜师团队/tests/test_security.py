from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.config import load_config
from feicai_seedance.utils import sanitize_episode_id


class TestSecurity(unittest.TestCase):
    def test_episode_sanitization_blocks_traversal(self) -> None:
        for payload in ["../ep01", "ep1", "ep001", "ep01/../../x"]:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    sanitize_episode_id(payload)

    def test_config_paths_are_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = Path(__file__).resolve().parents[1]
            shutil.copy2(source_root / "project-config.json", root / "project-config.json")
            rewritten = (root / "project-config.json").read_text(encoding="utf-8").replace('"script"', '"../script"')
            (root / "project-config.json").write_text(rewritten, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(root)

    def test_three_random_invalid_inputs(self) -> None:
        invalid_cases = ["ep-01", "episode01", "epab"]
        for payload in invalid_cases:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    sanitize_episode_id(payload)

    def test_unknown_model_provider_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = Path(__file__).resolve().parents[1]
            shutil.copy2(source_root / "project-config.json", root / "project-config.json")
            rewritten = (
                (root / "project-config.json")
                .read_text(encoding="utf-8")
                .replace('"provider": "codex"', '"provider": "missing-provider"', 1)
            )
            (root / "project-config.json").write_text(rewritten, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(root)

    def test_legacy_single_provider_config_still_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = Path(__file__).resolve().parents[1]
            shutil.copy2(source_root / "project-config.json", root / "project-config.json")
            payload = json.loads((root / "project-config.json").read_text(encoding="utf-8"))
            payload.pop("providers", None)
            for model in payload["models"].values():
                model.pop("provider", None)
            (root / "project-config.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            config = load_config(root)
            self.assertEqual(config.provider_name_for_model("director_generate"), "default")
            self.assertEqual(config.api_settings_for_model("director_generate").api_key_env, payload["api"]["api_key_env"])


if __name__ == "__main__":
    unittest.main()
