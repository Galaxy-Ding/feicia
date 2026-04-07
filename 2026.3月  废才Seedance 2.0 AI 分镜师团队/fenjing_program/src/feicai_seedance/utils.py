from __future__ import annotations

import json
import re
from pathlib import Path

EPISODE_PATTERN = re.compile(r"(ep\d{2})", re.IGNORECASE)
VALID_EPISODE_PATTERN = re.compile(r"^ep\d{2}$", re.IGNORECASE)


def extract_episode_id(value: str) -> str | None:
    match = EPISODE_PATTERN.search(value)
    if not match:
        return None
    return match.group(1).lower()


def sanitize_episode_id(value: str) -> str:
    cleaned = value.strip().lower()
    if not VALID_EPISODE_PATTERN.fullmatch(cleaned):
        raise ValueError(f"Invalid episode id: {value}")
    return cleaned


def choose_grid_spec(scene_count: int) -> str:
    if scene_count <= 0:
        raise ValueError("scene_count must be positive")
    if scene_count <= 9:
        return "3x3"
    if scene_count <= 12:
        return "3x4"
    if scene_count <= 16:
        return "4x4"
    raise ValueError("scene_count exceeds supported maximum of 16")


def extract_json_object(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in text")
    return json.loads(text[start : end + 1])


def safe_relative_path(root: Path, candidate: str) -> Path:
    path = (root / candidate).resolve()
    root_resolved = root.resolve()
    if root_resolved not in path.parents and path != root_resolved:
        raise ValueError(f"Path escapes project root: {candidate}")
    return path


def merge_issue_lists(*issue_groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in issue_groups:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged
