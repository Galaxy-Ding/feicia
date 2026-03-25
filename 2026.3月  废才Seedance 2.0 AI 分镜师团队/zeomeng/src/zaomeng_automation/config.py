from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .models import AppConfig


def safe_join_within(base_dir: Path, relative_path: str) -> Path:
    candidate = (base_dir / relative_path).resolve()
    resolved_base = base_dir.resolve()
    if candidate != resolved_base and resolved_base not in candidate.parents:
        raise ValueError(f"Path escapes workspace: {relative_path}")
    return candidate


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_app_config(path: Path) -> AppConfig:
    config_path = path.resolve()
    base_dir = config_path.parent.parent.parent
    raw = _read_json(config_path)

    config = AppConfig(
        base_dir=base_dir,
        project_name=raw["project_name"],
        jimeng_url=raw["jimeng_url"],
        profile_path=safe_join_within(base_dir, raw["profile_path"]),
        selectors_path=safe_join_within(base_dir, raw["selectors_path"]),
        prompt_path=safe_join_within(base_dir, raw["prompt_path"]),
        staging_root=safe_join_within(base_dir, raw["staging_root"]),
        images_root=safe_join_within(base_dir, raw["images_root"]),
        run_log_dir=safe_join_within(base_dir, raw["run_log_dir"]),
        error_log_dir=safe_join_within(base_dir, raw["error_log_dir"]),
        task_state_dir=safe_join_within(base_dir, raw["task_state_dir"]),
        browser_state_dir=safe_join_within(base_dir, raw["browser_state_dir"]),
        batch_id=raw["batch_id"],
        wait_timeout_seconds=int(raw["wait_timeout_seconds"]),
        poll_interval_seconds=int(raw["poll_interval_seconds"]),
        download_stable_checks=int(raw["download_stable_checks"]),
        max_slug_length=int(raw["max_slug_length"]),
        images_per_prompt=int(raw["images_per_prompt"]),
        login_markers=list(raw.get("login_markers", [])),
    )

    for directory in (
        config.profile_path,
        config.staging_root,
        config.images_root,
        config.run_log_dir,
        config.error_log_dir,
        config.task_state_dir,
        config.browser_state_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    return config
