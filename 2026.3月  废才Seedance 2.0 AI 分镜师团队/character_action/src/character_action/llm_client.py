from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


@dataclass(slots=True, frozen=True)
class LLMProviderSettings:
    name: str
    base_url: str
    api_key: str
    timeout_seconds: int = 300
    max_retries: int = 3
    wire_api: str = "responses"


@dataclass(slots=True, frozen=True)
class LLMModelSettings:
    name: str
    provider: str
    temperature: float
    max_tokens: int


class OpenAICompatibleClient:
    def __init__(self, settings: LLMProviderSettings) -> None:
        self.settings = settings

    def chat(self, model: LLMModelSettings, messages: list[dict[str, str]]) -> str:
        if self.settings.wire_api == "responses":
            return self._responses_api(model, messages)
        return self._chat_completions_api(model, messages)

    def _chat_completions_api(self, model: LLMModelSettings, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": model.name,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
            "messages": messages,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{normalize_openai_base_url(self.settings.base_url).rstrip('/')}/chat/completions",
            method="POST",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LLM gateway request failed: provider={self.settings.name} status={exc.code} body={details[:400]}"
            ) from exc
        return str(raw["choices"][0]["message"]["content"])

    def _responses_api(self, model: LLMModelSettings, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": model.name,
            "temperature": model.temperature,
            "max_output_tokens": model.max_tokens,
            "input": [
                {
                    "role": message["role"],
                    "content": [{"type": "input_text", "text": message["content"]}],
                }
                for message in messages
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url=f"{normalize_openai_base_url(self.settings.base_url).rstrip('/')}/responses",
            method="POST",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"LLM gateway request failed: provider={self.settings.name} status={exc.code} body={details[:400]}"
            ) from exc
        output_text = raw.get("output_text")
        if isinstance(output_text, str) and output_text:
            return output_text
        fragments: list[str] = []
        for item in raw.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str) and text:
                    fragments.append(text)
        if fragments:
            return "".join(fragments)
        raise RuntimeError("Responses API returned no text output")


class RoutedOpenAICompatibleClient:
    def __init__(self, providers: dict[str, LLMProviderSettings]) -> None:
        self.clients = {name: OpenAICompatibleClient(settings) for name, settings in providers.items()}
        self.providers = providers

    def chat(self, model: LLMModelSettings, messages: list[dict[str, str]]) -> str:
        client = self.clients.get(model.provider)
        if client is None:
            raise RuntimeError(f"Unknown provider '{model.provider}' for model '{model.name}'")
        last_error: Exception | None = None
        for _ in range(max(1, self.providers[model.provider].max_retries)):
            try:
                return client.chat(model, messages)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(f"Model call failed for provider '{model.provider}' model '{model.name}'") from last_error


def load_local_providers(config_path: Path) -> dict[str, LLMProviderSettings]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    providers_payload = payload.get("providers")
    if not isinstance(providers_payload, dict):
        raise ValueError(f"Invalid providers payload in {config_path}")
    providers: dict[str, LLMProviderSettings] = {}
    for name, provider_payload in providers_payload.items():
        if not isinstance(provider_payload, dict):
            continue
        base_url = str(provider_payload.get("base_url", "")).strip()
        api_key = str(provider_payload.get("api_key", "")).strip()
        if not base_url or not api_key:
            raise ValueError(f"Provider '{name}' in {config_path} requires base_url and api_key")
        providers[name] = LLMProviderSettings(name=name, base_url=base_url, api_key=api_key)
    if not providers:
        raise ValueError(f"No usable providers found in {config_path}")
    return providers


def default_local_provider_config(project_root: Path) -> Path:
    return (project_root.resolve().parent / "fenjing_program" / "project-config.local.json").resolve()


def normalize_openai_base_url(base_url: str) -> str:
    parsed = urlsplit(base_url.strip())
    path = parsed.path.rstrip("/")
    if not path:
        path = "/v1"
    if not path.endswith("/v1"):
        path = f"{path}/v1"
    return urlunsplit(parsed._replace(path=path))


def provider_key_from_env(var_name: str) -> str | None:
    value = os.environ.get(var_name)
    return value.strip() if value else None
