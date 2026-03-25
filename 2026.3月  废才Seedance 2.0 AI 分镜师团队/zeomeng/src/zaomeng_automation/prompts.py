from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, List

from .models import PromptTask
from .naming import make_task_id, slugify_prompt


def _normalize_prompts(items: Iterable[str]) -> List[str]:
    prompts = []
    for item in items:
        value = item.strip()
        if value:
            prompts.append(value)
    return prompts


def _load_json_prompts(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        if all(isinstance(item, str) for item in data):
            return _normalize_prompts(data)
        prompts = [str(item["prompt"]) for item in data if isinstance(item, dict) and item.get("prompt")]
        return _normalize_prompts(prompts)
    raise ValueError(f"Unsupported JSON prompt structure: {path}")


def _load_csv_prompts(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        prompts = []
        for row in reader:
            prompt = row.get("prompt") or row.get("text") or ""
            if prompt.strip():
                prompts.append(prompt)
        return _normalize_prompts(prompts)


def _load_markdown_prompts(path: Path) -> List[str]:
    prompts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(("- ", "* ")):
            prompts.append(line[2:])
    return _normalize_prompts(prompts)


def _load_text_prompts(path: Path) -> List[str]:
    return _normalize_prompts(path.read_text(encoding="utf-8").splitlines())


def load_prompt_tasks(path: Path, batch: str, max_slug_length: int = 48) -> List[PromptTask]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        prompts = _load_json_prompts(path)
    elif suffix == ".csv":
        prompts = _load_csv_prompts(path)
    elif suffix == ".md":
        prompts = _load_markdown_prompts(path)
    elif suffix in {".txt", ".text"}:
        prompts = _load_text_prompts(path)
    else:
        raise ValueError(f"Unsupported prompt file type: {path.suffix}")

    tasks = []
    for ordinal, prompt in enumerate(prompts, start=1):
        tasks.append(
            PromptTask(
                task_id=make_task_id(batch, ordinal),
                batch=batch,
                prompt=prompt,
                prompt_slug=slugify_prompt(prompt, max_length=max_slug_length),
            )
        )
    return tasks
