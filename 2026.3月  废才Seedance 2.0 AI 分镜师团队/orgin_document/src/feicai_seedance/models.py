from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ModelSettings:
    name: str
    temperature: float
    max_tokens: int
    provider: str | None = None


@dataclass(slots=True)
class ApiSettings:
    provider: str
    base_url: str
    api_key_env: str
    timeout_seconds: int
    max_retries: int
    wire_api: str = "chat_completions"
    api_key: str = ""


@dataclass(slots=True)
class RuntimePaths:
    root: Path
    scripts: Path
    assets: Path
    outputs: Path
    logs: Path
    sessions: Path
    reports: Path


@dataclass(slots=True)
class ProjectConfig:
    project_name: str
    language: str
    visual_style: str
    target_media: str
    command_prefix: str
    api: ApiSettings
    providers: dict[str, ApiSettings]
    models: dict[str, ModelSettings]
    review_max_auto_fix_rounds: int
    paths: RuntimePaths

    def provider_name_for_model(self, model_key: str) -> str:
        return self.models[model_key].provider or "default"

    def api_settings_for_model(self, model_key: str) -> ApiSettings:
        provider_name = self.provider_name_for_model(model_key)
        if provider_name not in self.providers:
            raise RuntimeError(f"Unknown provider '{provider_name}' for model '{model_key}'")
        return self.providers[provider_name]


@dataclass(slots=True)
class EpisodeStatus:
    episode: str
    script_file: Path | None
    stage: str
    director_analysis_exists: bool
    seedance_prompts_exists: bool
    character_assets_exist: bool
    scene_assets_exist: bool


@dataclass(slots=True)
class ReviewOutcome:
    result: str
    report: str
    issues: list[str] = field(default_factory=list)
    average_score: float | None = None
    has_item_below_6: bool | None = None
    dimension_scores: dict[str, float] = field(default_factory=dict)
    violations: list[dict[str, Any]] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    role: str
    episode: str
    history_path: Path
