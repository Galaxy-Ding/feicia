from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from character_action.llm_client import load_local_providers, normalize_openai_base_url


class LLMClientConfigTest(unittest.TestCase):
    def test_normalize_openai_base_url_appends_v1(self) -> None:
        self.assertEqual(normalize_openai_base_url("http://example.com"), "http://example.com/v1")
        self.assertEqual(normalize_openai_base_url("http://example.com/v1"), "http://example.com/v1")

    def test_load_local_providers_reads_plain_local_override_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "project-config.local.json"
            path.write_text(
                json.dumps(
                    {
                        "providers": {
                            "codex": {"base_url": "http://router.local:6543", "api_key": "sk-codex"},
                            "claude": {"base_url": "http://router.local:6543/v1", "api_key": "sk-claude"},
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            providers = load_local_providers(path)
        self.assertEqual(set(providers), {"codex", "claude"})
        self.assertEqual(providers["codex"].api_key, "sk-codex")
        self.assertEqual(providers["claude"].base_url, "http://router.local:6543/v1")


if __name__ == "__main__":
    unittest.main()
