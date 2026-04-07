from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .workspace import WorkspacePaths, resolve_episode_paths


_EPISODE_RE = re.compile(r"^(?:ep)?(\d{1,4})$", re.IGNORECASE)


def normalize_episode_id(raw: str) -> str:
    text = raw.strip().lower()
    match = _EPISODE_RE.fullmatch(text)
    if not match:
        raise ValueError(f"Invalid episode id: {raw!r}")
    digits = match.group(1)
    width = max(2, len(digits))
    return f"ep{int(digits):0{width}d}"


def build_task_id(phase: str, episode_id: str, stage: str) -> str:
    normalized_episode = normalize_episode_id(episode_id)
    phase_name = phase.strip().lower().replace("_", "-")
    stage_name = stage.strip().lower().replace("_", "-")
    if not phase_name or not stage_name:
        raise ValueError("phase and stage must be non-empty")
    return f"{phase_name}-{normalized_episode}-{stage_name}"


def build_episode_task(
    book_id: str,
    episode_id: str,
    *,
    phase: str = "phase01",
    stage: str = "integration",
    manual_checkpoints: int = 1,
    upstream: Iterable[str] | None = None,
) -> dict[str, object]:
    if not book_id.strip():
        raise ValueError("book_id must be non-empty")
    if manual_checkpoints < 0:
        raise ValueError("manual_checkpoints must be >= 0")
    normalized_episode = normalize_episode_id(episode_id)
    return {
        "project_id": "video_only_once",
        "book_id": book_id.strip(),
        "episode_id": normalized_episode,
        "phase": phase,
        "stage": stage,
        "task_id": build_task_id(phase, normalized_episode, stage),
        "upstream": list(upstream or []),
        "manual_checkpoints": manual_checkpoints,
    }


def build_phase2_episode_manifest(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
    *,
    browser: str = "mock",
) -> dict[str, object]:
    if not book_id.strip():
        raise ValueError("book_id must be non-empty")
    episode = resolve_episode_paths(workspace, episode_id)
    return {
        "project_id": "video_only_once",
        "book_id": book_id.strip(),
        "episode_id": episode.episode_id,
        "phase": "phase02",
        "stage": "character_anchor",
        "task_id": build_task_id("phase02", episode.episode_id, "character_anchor"),
        "upstream": [build_task_id("phase01", episode.episode_id, "integration")],
        "manual_checkpoints": 2,
        "character_system": build_character_system_entry(workspace, book_id),
        "knowledge_base": build_knowledge_base_entry(workspace),
        "character_anchor": build_character_anchor_entry(workspace, episode.episode_id),
        "image_generation": build_image_generation_entry(workspace, episode.episode_id, browser=browser),
        "registry_writeback": build_registry_writeback_entry(workspace, episode.episode_id),
    }


def build_character_system_entry(workspace: WorkspacePaths, book_id: str) -> dict[str, object]:
    safe_book_id = _normalize_book_id(book_id)
    return {
        "root": _relative_path(workspace, workspace.character_action_root),
        "config": _relative_path(workspace, workspace.character_action_configs_root / "dev.yaml"),
        "raw_books_root": _relative_path(workspace, workspace.character_action_raw_books_root),
        "normalized_root": _relative_path(workspace, workspace.character_action_normalized_root),
        "exports_root": _relative_path(workspace, workspace.character_action_exports_root),
        "book_outputs": {
            "normalized_json": _relative_path(
                workspace,
                workspace.character_action_normalized_root / f"{safe_book_id}.json",
            ),
            "character_cards": _relative_path(
                workspace,
                workspace.character_action_exports_root / safe_book_id / "character_cards.json",
            ),
            "review_queue": _relative_path(
                workspace,
                workspace.character_action_exports_root / safe_book_id / "review_queue.json",
            ),
        },
    }


def build_knowledge_base_entry(workspace: WorkspacePaths) -> dict[str, object]:
    return {
        "root": _relative_path(workspace, workspace.fenjing_knowledge_base_root),
        "entities": {
            "characters": _relative_path(
                workspace,
                workspace.fenjing_knowledge_base_root / "entities" / "characters.json",
            ),
        },
        "documents": {
            "character_bible": _relative_path(
                workspace,
                workspace.fenjing_knowledge_base_root / "character_bible.md",
            ),
            "visual_motifs": _relative_path(
                workspace,
                workspace.fenjing_knowledge_base_root / "visual_motifs.md",
            ),
        },
        "style_presets_root": _relative_path(workspace, workspace.fenjing_style_presets_root),
    }


def build_character_anchor_entry(workspace: WorkspacePaths, episode_id: str) -> dict[str, object]:
    episode = resolve_episode_paths(workspace, episode_id)
    return {
        "output_root": _relative_path(workspace, episode.character_root),
        "outputs": {
            "candidate_list": _relative_path(workspace, episode.character_candidate_list_path),
            "character_sheets_json": _relative_path(workspace, episode.character_sheets_json_path),
            "character_sheets_md": _relative_path(workspace, episode.character_sheets_md_path),
            "character_image_tasks": _relative_path(workspace, episode.character_image_tasks_path),
            "character_image_run": _relative_path(workspace, episode.character_image_run_path),
            "character_review_json": _relative_path(workspace, episode.character_review_json_path),
            "character_review_md": _relative_path(workspace, episode.character_review_md_path),
            "character_anchor_pack": _relative_path(workspace, episode.character_anchor_pack_path),
            "character_reference_pack": _relative_path(workspace, episode.character_reference_pack_path),
        },
    }


def build_image_generation_entry(
    workspace: WorkspacePaths,
    episode_id: str,
    *,
    browser: str,
) -> dict[str, object]:
    episode = resolve_episode_paths(workspace, episode_id)
    return {
        "browser": browser,
        "task_manifest": _relative_path(workspace, episode.character_image_tasks_path),
        "run_report": _relative_path(workspace, episode.character_image_run_path),
        "staging_root": _relative_path(workspace, episode.zaomeng_character_staging_root),
        "images_root": _relative_path(workspace, episode.zaomeng_character_images_root),
        "zaomeng_config": _relative_path(workspace, workspace.zaomeng_root / "workflow" / "configs" / "project.json"),
    }


def build_registry_writeback_entry(workspace: WorkspacePaths, episode_id: str) -> dict[str, object]:
    episode = resolve_episode_paths(workspace, episode_id)
    return {
        "asset_registry": _relative_path(workspace, workspace.asset_registry_path),
        "character_index": _relative_path(workspace, workspace.character_index_path),
        "scene_index": _relative_path(workspace, workspace.scene_index_path),
        "image_generation_log": _relative_path(workspace, workspace.image_generation_log_path),
        "reference_map": _relative_path(workspace, episode.reference_map_path),
        "anchor_pack": _relative_path(workspace, episode.character_anchor_pack_path),
        "reference_pack": _relative_path(workspace, episode.character_reference_pack_path),
    }


def decide_gate(
    episode_id: str,
    stage: str,
    *,
    passed: bool,
    manual_required: bool,
    retryable: bool,
    reason_codes: Iterable[str] | None = None,
) -> dict[str, object]:
    normalized_episode = normalize_episode_id(episode_id)
    reasons = list(reason_codes or [])
    if passed:
        decision = "AUTO_CONTINUE"
    elif manual_required:
        decision = "MANUAL_REVIEW"
    elif retryable:
        decision = "RETRY"
    else:
        decision = "BLOCKED"
    return {
        "episode_id": normalized_episode,
        "stage": stage,
        "decision": decision,
        "manual_required": manual_required,
        "retryable": retryable,
        "reason_codes": reasons,
    }


def _relative_path(workspace: WorkspacePaths, path: Path) -> str:
    return str(path.resolve().relative_to(workspace.project_root)).replace("\\", "/")


def _normalize_book_id(raw: str) -> str:
    text = raw.strip().lower().replace(" ", "_")
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text if text.startswith("book_") else f"book_{text}"
