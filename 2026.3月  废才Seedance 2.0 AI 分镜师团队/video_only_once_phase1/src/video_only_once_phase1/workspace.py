from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspacePaths:
    project_root: Path
    phase1_root: Path
    character_action_root: Path
    fenjing_root: Path
    zaomeng_root: Path
    character_action_configs_root: Path
    character_action_data_root: Path
    character_action_raw_books_root: Path
    character_action_normalized_root: Path
    character_action_exports_root: Path
    fenjing_project_data_root: Path
    fenjing_knowledge_base_root: Path
    fenjing_style_presets_root: Path
    fenjing_outputs_root: Path
    fenjing_assets_root: Path
    asset_registry_root: Path
    asset_library_root: Path
    asset_manifests_root: Path
    asset_registry_path: Path
    character_index_path: Path
    scene_index_path: Path
    image_generation_log_path: Path
    zaomeng_downloads_root: Path
    runtime_root: Path
    logs_root: Path
    manifests_root: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class EpisodePaths:
    episode_id: str
    fenjing_episode_root: Path
    character_root: Path
    character_candidate_list_path: Path
    character_sheets_json_path: Path
    character_sheets_md_path: Path
    character_image_tasks_path: Path
    character_image_run_path: Path
    character_review_json_path: Path
    character_review_md_path: Path
    character_anchor_pack_path: Path
    character_reference_pack_path: Path
    reference_map_path: Path
    zaomeng_character_staging_root: Path
    zaomeng_character_images_root: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


def ensure_within_root(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    resolved_candidate.relative_to(resolved_root)
    return resolved_candidate


def resolve_workspace(project_root: Path) -> WorkspacePaths:
    root = project_root.resolve()
    phase1_root = ensure_within_root(root, root / "video_only_once_phase1")
    character_action_root = ensure_within_root(root, root / "character_action")
    fenjing_root = ensure_within_root(root, root / "fenjing_program")
    zaomeng_root = ensure_within_root(root, root / "zaomeng")
    character_action_configs_root = ensure_within_root(root, character_action_root / "configs")
    character_action_data_root = ensure_within_root(root, character_action_root / "data")
    character_action_raw_books_root = ensure_within_root(root, character_action_data_root / "raw_books")
    character_action_normalized_root = ensure_within_root(root, character_action_data_root / "normalized")
    character_action_exports_root = ensure_within_root(root, character_action_data_root / "exports")
    fenjing_project_data_root = ensure_within_root(root, fenjing_root / "project_data")
    fenjing_knowledge_base_root = ensure_within_root(root, fenjing_project_data_root / "knowledge_base")
    fenjing_style_presets_root = ensure_within_root(root, fenjing_project_data_root / "style_presets")
    fenjing_outputs_root = ensure_within_root(root, fenjing_root / "outputs")
    fenjing_assets_root = ensure_within_root(root, fenjing_root / "assets")
    asset_registry_root = ensure_within_root(root, fenjing_assets_root / "registry")
    asset_library_root = ensure_within_root(root, fenjing_assets_root / "library")
    asset_manifests_root = ensure_within_root(root, fenjing_assets_root / "manifests")
    zaomeng_downloads_root = ensure_within_root(root, zaomeng_root / "downloads")
    runtime_root = ensure_within_root(root, phase1_root / "runtime")
    logs_root = ensure_within_root(root, runtime_root / "logs")
    manifests_root = ensure_within_root(root, runtime_root / "manifests")
    return WorkspacePaths(
        project_root=root,
        phase1_root=phase1_root,
        character_action_root=character_action_root,
        fenjing_root=fenjing_root,
        zaomeng_root=zaomeng_root,
        character_action_configs_root=character_action_configs_root,
        character_action_data_root=character_action_data_root,
        character_action_raw_books_root=character_action_raw_books_root,
        character_action_normalized_root=character_action_normalized_root,
        character_action_exports_root=character_action_exports_root,
        fenjing_project_data_root=fenjing_project_data_root,
        fenjing_knowledge_base_root=fenjing_knowledge_base_root,
        fenjing_style_presets_root=fenjing_style_presets_root,
        fenjing_outputs_root=fenjing_outputs_root,
        fenjing_assets_root=fenjing_assets_root,
        asset_registry_root=asset_registry_root,
        asset_library_root=asset_library_root,
        asset_manifests_root=asset_manifests_root,
        asset_registry_path=ensure_within_root(root, asset_registry_root / "asset-registry.json"),
        character_index_path=ensure_within_root(root, asset_registry_root / "character-index.json"),
        scene_index_path=ensure_within_root(root, asset_registry_root / "scene-index.json"),
        image_generation_log_path=ensure_within_root(root, asset_manifests_root / "image-generation-log.jsonl"),
        zaomeng_downloads_root=zaomeng_downloads_root,
        runtime_root=runtime_root,
        logs_root=logs_root,
        manifests_root=manifests_root,
    )


def resolve_episode_paths(workspace: WorkspacePaths, episode_id: str) -> EpisodePaths:
    from .contracts import normalize_episode_id

    normalized_episode = normalize_episode_id(episode_id)
    fenjing_episode_root = ensure_within_root(workspace.project_root, workspace.fenjing_outputs_root / normalized_episode)
    character_root = ensure_within_root(workspace.project_root, fenjing_episode_root / "characters")
    zaomeng_character_staging_root = ensure_within_root(
        workspace.project_root,
        workspace.zaomeng_downloads_root / "staging" / "characters" / normalized_episode,
    )
    zaomeng_character_images_root = ensure_within_root(
        workspace.project_root,
        workspace.zaomeng_downloads_root / "images" / "characters" / normalized_episode,
    )
    return EpisodePaths(
        episode_id=normalized_episode,
        fenjing_episode_root=fenjing_episode_root,
        character_root=character_root,
        character_candidate_list_path=ensure_within_root(workspace.project_root, character_root / "character-candidate-list.json"),
        character_sheets_json_path=ensure_within_root(workspace.project_root, character_root / "character-sheets.json"),
        character_sheets_md_path=ensure_within_root(workspace.project_root, character_root / "character-sheets.md"),
        character_image_tasks_path=ensure_within_root(workspace.project_root, character_root / "character-image-tasks.json"),
        character_image_run_path=ensure_within_root(workspace.project_root, character_root / "character-image-run.json"),
        character_review_json_path=ensure_within_root(workspace.project_root, character_root / "character-review.json"),
        character_review_md_path=ensure_within_root(workspace.project_root, character_root / "character-review.md"),
        character_anchor_pack_path=ensure_within_root(workspace.project_root, character_root / "character-anchor-pack.json"),
        character_reference_pack_path=ensure_within_root(workspace.project_root, character_root / "character-reference-pack.json"),
        reference_map_path=ensure_within_root(workspace.project_root, fenjing_episode_root / "reference-map.json"),
        zaomeng_character_staging_root=zaomeng_character_staging_root,
        zaomeng_character_images_root=zaomeng_character_images_root,
    )


def prepare_runtime_dirs(workspace: WorkspacePaths) -> list[Path]:
    created = []
    for path in (workspace.runtime_root, workspace.logs_root, workspace.manifests_root):
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created
