from __future__ import annotations

import json
from pathlib import Path

from .models import ApiSettings, ModelSettings, ProjectConfig, RuntimePaths
from .utils import safe_relative_path

LOCAL_CONFIG_FILENAME = "project-config.local.json"


def load_config(project_root: Path) -> ProjectConfig:
    config_path = project_root / "project-config.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    local_overrides = _load_local_overrides(project_root)
    default_api = _build_api_settings(raw["api"], local_overrides.get("api", {}), "api")
    providers = {"default": default_api}
    for provider_name, provider_settings in raw.get("providers", {}).items():
        if provider_name == "default":
            raise ValueError("providers.default is reserved; use top-level api instead")
        provider_override = local_overrides.get("providers", {}).get(provider_name, {})
        providers[provider_name] = _build_api_settings(
            provider_settings,
            provider_override,
            f"providers.{provider_name}",
        )

    root = project_root.resolve()
    paths = RuntimePaths(
        root=root,
        scripts=safe_relative_path(root, raw["paths"]["scripts"]),
        assets=safe_relative_path(root, raw["paths"]["assets"]),
        outputs=safe_relative_path(root, raw["paths"]["outputs"]),
        logs=safe_relative_path(root, raw["paths"]["logs"]),
        sessions=safe_relative_path(root, raw["paths"]["sessions"]),
        reports=safe_relative_path(root, raw["paths"]["reports"]),
    )

    models = {key: ModelSettings(**value) for key, value in raw["models"].items()}
    for model_key, model in models.items():
        if model.provider and model.provider not in providers:
            raise ValueError(f"Unknown provider '{model.provider}' configured for model '{model_key}'")

    return ProjectConfig(
        project_name=raw["project_name"],
        language=raw["language"],
        visual_style=raw["visual_style"],
        target_media=raw["target_media"],
        command_prefix=raw["command_prefix"],
        api=default_api,
        providers=providers,
        models=models,
        review_max_auto_fix_rounds=raw["review"]["max_auto_fix_rounds"],
        paths=paths,
    )


def ensure_runtime_directories(config: ProjectConfig) -> None:
    for path in (
        config.paths.scripts,
        config.paths.assets,
        config.paths.outputs,
        config.paths.logs,
        config.paths.sessions,
        config.paths.reports,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _load_local_overrides(project_root: Path) -> dict:
    path = project_root / LOCAL_CONFIG_FILENAME
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    overrides: dict[str, dict] = {}

    if isinstance(payload.get("api"), dict):
        overrides["api"] = dict(payload["api"])

    if any(key in payload for key in ("base_url", "api_key")):
        overrides.setdefault("api", {}).update(
            {key: payload[key] for key in ("base_url", "api_key") if isinstance(payload.get(key), str)}
        )

    providers = payload.get("providers", {})
    if isinstance(providers, dict):
        overrides["providers"] = {name: value for name, value in providers.items() if isinstance(value, dict)}

    return overrides


def _build_api_settings(base_payload: dict, override_payload: dict, label: str) -> ApiSettings:
    merged = dict(base_payload)
    if override_payload:
        for key in ("base_url", "api_key"):
            value = override_payload.get(key)
            if isinstance(value, str) and value.strip():
                merged[key] = value.strip()

    settings = ApiSettings(**merged)
    if _looks_like_secret(settings.api_key_env):
        raise ValueError(
            f"{label}.api_key_env must reference an environment variable name, not a raw API key. "
            f"Move the secret into {LOCAL_CONFIG_FILENAME} or an environment variable."
        )
    return settings


def _looks_like_secret(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith(("sk-", "sk_", "sess-"))
