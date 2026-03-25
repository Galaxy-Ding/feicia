from __future__ import annotations

import json
from pathlib import Path

from .acceptance_store import get_stage_status
from .artifact_utils import has_episode_block
from .models import EpisodeStatus, ProjectConfig
from .utils import extract_episode_id


def find_script_files(scripts_dir: Path) -> dict[str, Path]:
    results: dict[str, Path] = {}
    for path in sorted(scripts_dir.glob("*")):
        if not path.is_file():
            continue
        episode = extract_episode_id(path.name)
        if episode:
            results[episode] = path
    return results


def detect_episode_status(config: ProjectConfig, episode: str, script_file: Path | None) -> EpisodeStatus:
    output_dir = config.paths.outputs / episode
    director_file = output_dir / "01-director-analysis.md"
    seedance_file = output_dir / "02-seedance-prompts.md"
    reference_map_file = output_dir / "reference-map.json"
    character_assets = config.paths.assets / "character-prompts.md"
    scene_assets = config.paths.assets / "scene-prompts.md"
    character_ready = has_episode_block(character_assets, episode, "CHARACTER")
    scene_ready = has_episode_block(scene_assets, episode, "SCENE")
    registry_ready = _episode_registry_ready(config.paths.assets, episode)
    reference_map_ready = _reference_map_ready(reference_map_file)
    director_acceptance = get_stage_status(config.paths.reports, episode, "director")
    design_acceptance = get_stage_status(config.paths.reports, episode, "design")
    prompt_acceptance = get_stage_status(config.paths.reports, episode, "prompt")

    if script_file is None:
        stage = "WAIT_SCRIPT"
    elif not director_file.exists():
        stage = "DIRECTOR_ANALYSIS"
    elif director_acceptance != "accepted":
        stage = "DIRECTOR_REVIEW_PENDING"
    elif not character_ready or not scene_ready:
        stage = "ART_DESIGN"
    elif design_acceptance != "accepted":
        stage = "ART_REVIEW_PENDING"
    elif not registry_ready:
        stage = "IMAGE_PENDING"
    elif not reference_map_ready:
        stage = "REFERENCE_MAPPING_PENDING"
    elif not seedance_file.exists():
        stage = "STORYBOARD"
    elif prompt_acceptance != "accepted":
        stage = "STORYBOARD_REVIEW_PENDING"
    else:
        stage = "DONE"

    return EpisodeStatus(
        episode=episode,
        script_file=script_file,
        stage=stage,
        director_analysis_exists=director_file.exists(),
        seedance_prompts_exists=seedance_file.exists(),
        character_assets_exist=character_ready,
        scene_assets_exist=scene_ready,
    )


def detect_all_statuses(config: ProjectConfig) -> list[EpisodeStatus]:
    scripts = find_script_files(config.paths.scripts)
    episodes = sorted(scripts.keys())
    return [detect_episode_status(config, episode, scripts.get(episode)) for episode in episodes]


def pick_default_episode(statuses: list[EpisodeStatus]) -> str | None:
    for item in statuses:
        if item.stage != "DONE":
            return item.episode
    return statuses[0].episode if statuses else None


def _episode_registry_ready(assets_root: Path, episode: str) -> bool:
    registry_path = assets_root / "registry" / "asset-registry.json"
    if not registry_path.exists():
        return False
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    episode_assets = [item for item in payload.get("assets", []) if item.get("episode_origin") == episode]
    if not episode_assets:
        return False
    has_character = any(item.get("asset_type") == "character" and item.get("status") == "READY_FOR_STORYBOARD" for item in episode_assets)
    has_scene_panel = any(item.get("asset_type") == "scene_panel" and item.get("status") == "READY_FOR_STORYBOARD" for item in episode_assets)
    return has_character and has_scene_panel


def _reference_map_ready(reference_map_file: Path) -> bool:
    if not reference_map_file.exists():
        return False
    payload = json.loads(reference_map_file.read_text(encoding="utf-8"))
    return bool(payload.get("references")) and not payload.get("missing_assets")
