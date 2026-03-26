from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Tuple

import pytest


def _write_prompt_file(path: Path, prompts: Iterable[str]) -> None:
    prompts = list(prompts)
    if path.suffix == ".json":
        path.write_text(
            json.dumps([{"prompt": prompt} for prompt in prompts], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return
    if path.suffix == ".csv":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["prompt"])
            writer.writeheader()
            for prompt in prompts:
                writer.writerow({"prompt": prompt})
        return
    if path.suffix == ".md":
        path.write_text("\n".join(f"- {prompt}" for prompt in prompts), encoding="utf-8")
        return
    if path.suffix in {".txt", ".text"}:
        path.write_text("\n".join(prompts), encoding="utf-8")
        return
    raise ValueError(f"Unsupported prompt suffix: {path.suffix}")


def create_temp_project(tmp_path: Path, prompt_name: str, prompts: Iterable[str], batch_id: str = "img001") -> Tuple[Path, Path]:
    for directory in (
        tmp_path / "workflow" / "configs",
        tmp_path / "workflow" / "selectors",
        tmp_path / "workflow" / "prompts",
        tmp_path / "downloads" / "staging",
        tmp_path / "downloads" / "images",
        tmp_path / "logs" / "runs",
        tmp_path / "logs" / "errors",
        tmp_path / "state" / "tasks",
        tmp_path / "state" / "browser",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    prompt_path = tmp_path / "workflow" / "prompts" / prompt_name
    _write_prompt_file(prompt_path, prompts)

    selector_path = tmp_path / "workflow" / "selectors" / "jimeng-image-page.json"
    selector_path.write_text(
        json.dumps(
            {
                "elements": [
                    {"name": "image_generation_entry", "primary_selector": "text=图片生成"},
                    {"name": "prompt_input", "primary_selector": "textarea"},
                    {"name": "generate_button", "primary_selector": "text=生成"},
                    {"name": "download_button", "primary_selector": "text=下载"},
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    config = {
        "project_name": "即梦 2.0 浏览器自动化项目一期",
        "jimeng_url": "https://jimeng.jianying.com/",
        "generation_url": "https://jimeng.jianying.com/ai-tool/image/generate",
        "profile_path": "state/browser/mock-profile",
        "selectors_path": "workflow/selectors/jimeng-image-page.json",
        "prompt_path": f"workflow/prompts/{prompt_name}",
        "staging_root": "downloads/staging",
        "images_root": "downloads/images",
        "run_log_dir": "logs/runs",
        "error_log_dir": "logs/errors",
        "task_state_dir": "state/tasks",
        "browser_state_dir": "state/browser",
        "batch_id": batch_id,
        "wait_timeout_seconds": 600,
        "poll_interval_seconds": 1,
        "download_stable_checks": 1,
        "max_slug_length": 48,
        "images_per_prompt": 4,
        "openclaw_browser_profile": "openclaw",
        "login_markers": ["头像", "创作中心", "图片生成"],
    }
    config_path = tmp_path / "workflow" / "configs" / "project.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path, prompt_path


@pytest.fixture
def temp_project_factory(tmp_path: Path):
    def factory(prompt_name: str, prompts: Iterable[str], batch_id: str = "img001") -> Tuple[Path, Path]:
        return create_temp_project(tmp_path, prompt_name=prompt_name, prompts=prompts, batch_id=batch_id)

    return factory
