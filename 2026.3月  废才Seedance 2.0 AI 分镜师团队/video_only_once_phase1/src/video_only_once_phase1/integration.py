from __future__ import annotations

import shlex

from .contracts import normalize_episode_id
from .workspace import WorkspacePaths


ALLOWED_BROWSERS = {"mock", "openclaw"}
PYTHON_BIN = "python3"


def build_character_action_prepare_command(workspace: WorkspacePaths) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "character_action.cli",
        "--project-root",
        str(workspace.character_action_root),
        "prepare",
    ]


def build_character_action_doctor_command(workspace: WorkspacePaths) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "character_action.cli",
        "--project-root",
        str(workspace.character_action_root),
        "doctor",
    ]


def build_character_action_preprocess_command(
    workspace: WorkspacePaths,
    book_id: str,
    title: str,
    language: str,
    input_path: str,
    engine_mode: str = "auto",
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "character_action.cli",
        "--project-root",
        str(workspace.character_action_root),
        "preprocess-book",
        "--book-id",
        book_id,
        "--title",
        title,
        "--language",
        language,
        "--input",
        input_path,
        "--engine-mode",
        engine_mode,
    ]


def build_character_action_extract_command(workspace: WorkspacePaths, book_id: str) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "character_action.cli",
        "--project-root",
        str(workspace.character_action_root),
        "extract-characters",
        "--book-id",
        book_id,
    ]


def build_fenjing_status_command(workspace: WorkspacePaths) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "status",
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_prompt_command(workspace: WorkspacePaths, episode_id: str) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "prompt",
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_zaomeng_run_command(workspace: WorkspacePaths, browser: str) -> list[str]:
    if browser not in ALLOWED_BROWSERS:
        raise ValueError(f"Unsupported browser: {browser}")
    return [
        PYTHON_BIN,
        "-m",
        "zaomeng_automation.cli",
        "run",
        "--config",
        str(workspace.zaomeng_root / "workflow" / "configs" / "project.json"),
        "--browser",
        browser,
    ]


def build_fenjing_extract_characters_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "extract-characters",
        book_id,
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_build_character_sheets_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "build-character-sheets",
        book_id,
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_export_character_image_tasks_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "export-character-image-tasks",
        book_id,
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_generate_character_images_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
    browser: str,
) -> list[str]:
    if browser not in ALLOWED_BROWSERS:
        raise ValueError(f"Unsupported browser: {browser}")
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "generate-character-images",
        book_id,
        normalize_episode_id(episode_id),
        "--browser",
        browser,
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_review_character_images_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "review-character-images",
        book_id,
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_approve_character_assets_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "approve-character-assets",
        book_id,
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_export_character_reference_pack_command(
    workspace: WorkspacePaths,
    book_id: str,
    episode_id: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "export-character-reference-pack",
        book_id,
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_register_image_command(
    workspace: WorkspacePaths,
    episode_id: str,
    asset_id: str,
    image_path: str,
) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "register-image",
        normalize_episode_id(episode_id),
        asset_id,
        image_path,
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_fenjing_build_reference_map_command(workspace: WorkspacePaths, episode_id: str) -> list[str]:
    return [
        PYTHON_BIN,
        "-m",
        "feicai_seedance.cli",
        "build-reference-map",
        normalize_episode_id(episode_id),
        "--project-root",
        str(workspace.fenjing_root),
    ]


def build_bridge_commands(
    workspace: WorkspacePaths,
    *,
    book_id: str = "demo-book",
    episode_id: str,
    browser: str,
    asset_id: str = "ASSET_ID",
    image_path: str = "IMAGE_PATH",
    title: str = "BOOK_TITLE",
    language: str = "zh",
    input_path: str = "data/raw_books/BOOK.txt",
    engine_mode: str = "auto",
) -> dict[str, list[str]]:
    return {
        "character_action_prepare": build_character_action_prepare_command(workspace),
        "character_action_doctor": build_character_action_doctor_command(workspace),
        "character_action_preprocess": build_character_action_preprocess_command(
            workspace,
            book_id,
            title,
            language,
            input_path,
            engine_mode=engine_mode,
        ),
        "character_action_extract": build_character_action_extract_command(workspace, book_id),
        "fenjing_status": build_fenjing_status_command(workspace),
        "fenjing_prompt": build_fenjing_prompt_command(workspace, episode_id),
        "character_extract": build_fenjing_extract_characters_command(workspace, book_id, episode_id),
        "character_build_sheets": build_fenjing_build_character_sheets_command(workspace, book_id, episode_id),
        "character_export_image_tasks": build_fenjing_export_character_image_tasks_command(workspace, book_id, episode_id),
        "character_generate_images": build_fenjing_generate_character_images_command(workspace, book_id, episode_id, browser),
        "character_review_images": build_fenjing_review_character_images_command(workspace, book_id, episode_id),
        "character_approve_assets": build_fenjing_approve_character_assets_command(workspace, book_id, episode_id),
        "character_export_reference_pack": build_fenjing_export_character_reference_pack_command(workspace, book_id, episode_id),
        "register_image": build_fenjing_register_image_command(workspace, episode_id, asset_id, image_path),
        "build_reference_map": build_fenjing_build_reference_map_command(workspace, episode_id),
        "zaomeng_run": build_zaomeng_run_command(workspace, browser),
    }


def shellify(commands: dict[str, list[str]]) -> dict[str, str]:
    return {key: " ".join(shlex.quote(part) for part in value) for key, value in commands.items()}
