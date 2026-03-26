from __future__ import annotations

import os
import unittest

from feicai_seedance.llm_client import OpenAICompatibleClient, normalize_openai_base_url
from feicai_seedance.models import ApiSettings, ModelSettings


class TestLLMClient(unittest.TestCase):
    def test_normalize_openai_base_url_appends_v1(self) -> None:
        self.assertEqual(normalize_openai_base_url("http://example.com"), "http://example.com/v1")
        self.assertEqual(normalize_openai_base_url("http://example.com/v1"), "http://example.com/v1")

    def test_local_api_key_override_takes_priority(self) -> None:
        os.environ["CCSWITCH_TEST_API_KEY"] = "sk-env-value"
        try:
            client = OpenAICompatibleClient(
                ApiSettings(
                    provider="openai-compatible",
                    base_url="http://example.com",
                    api_key_env="CCSWITCH_TEST_API_KEY",
                    timeout_seconds=30,
                    max_retries=1,
                    api_key="sk-local-value",
                )
            )
            self.assertEqual(client._resolve_api_key(), "sk-local-value")
        finally:
            os.environ.pop("CCSWITCH_TEST_API_KEY", None)

    def test_missing_api_key_raises_clear_error(self) -> None:
        client = OpenAICompatibleClient(
            ApiSettings(
                provider="openai-compatible",
                base_url="http://example.com",
                api_key_env="CCSWITCH_TEST_API_KEY",
                timeout_seconds=30,
                max_retries=1,
            )
        )
        model = ModelSettings(name="gpt-test", temperature=0.1, max_tokens=128)

        with self.assertRaises(RuntimeError) as context:
            client.chat(model, [{"role": "user", "content": "hi"}])

        self.assertIn("project-config.local.json", str(context.exception))


if __name__ == "__main__":
    unittest.main()
