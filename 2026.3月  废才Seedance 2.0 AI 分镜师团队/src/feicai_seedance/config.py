from __future__ import annotations

import json
from pathlib import Path

from .models import ApiSettings, ModelSettings, ProjectConfig, RuntimePaths
from .utils import safe_relative_path


def load_config(project_root: Path) -> ProjectConfig:
    config_path = project_root / "project-config.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    default_api = ApiSettings(**raw["api"])
    providers = {"default": default_api}
    for provider_name, provider_settings in raw.get("providers", {}).items():
        if provider_name == "default":
            raise ValueError("providers.default is reserved; use top-level api instead")
        providers[provider_name] = ApiSettings(**provider_settings)

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
