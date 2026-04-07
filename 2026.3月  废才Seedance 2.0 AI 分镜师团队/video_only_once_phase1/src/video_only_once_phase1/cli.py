from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import build_episode_task, build_phase2_episode_manifest, normalize_episode_id
from .integration import build_bridge_commands, shellify
from .workspace import prepare_runtime_dirs, resolve_episode_paths, resolve_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VideoOnlyOnce phase1 integration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project-root", default=".")

    status_parser = subparsers.add_parser("status", parents=[common], help="show workspace status")
    status_parser.add_argument("--episode", default="ep01")

    prepare_parser = subparsers.add_parser("prepare", parents=[common], help="prepare runtime directories")
    prepare_parser.add_argument("--book-id", default="demo-book")
    prepare_parser.add_argument("--episode", default="ep01")
    prepare_parser.add_argument("--browser", default="mock")

    commands_parser = subparsers.add_parser("show-commands", parents=[common], help="show bridge commands")
    commands_parser.add_argument("--book-id", default="demo-book")
    commands_parser.add_argument("--title", default="BOOK_TITLE")
    commands_parser.add_argument("--language", default="zh")
    commands_parser.add_argument("--input-path", default="data/raw_books/BOOK.txt")
    commands_parser.add_argument("--engine-mode", default="auto")
    commands_parser.add_argument("--episode", default="ep01")
    commands_parser.add_argument("--browser", default="mock")
    commands_parser.add_argument("--asset-id", default="ASSET_ID")
    commands_parser.add_argument("--image-path", default="IMAGE_PATH")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = resolve_workspace(Path(args.project_root))

    if args.command == "status":
        episode = resolve_episode_paths(workspace, args.episode)
        payload = {
            "workspace": workspace.to_dict(),
            "episode": episode.to_dict(),
            "episode_id": normalize_episode_id(args.episode),
            "character_action_exists": workspace.character_action_root.exists(),
            "fenjing_exists": workspace.fenjing_root.exists(),
            "zaomeng_exists": workspace.zaomeng_root.exists(),
            "phase2": {
                "character_action_configs_exists": workspace.character_action_configs_root.exists(),
                "character_action_raw_books_exists": workspace.character_action_raw_books_root.exists(),
                "knowledge_base_exists": workspace.fenjing_knowledge_base_root.exists(),
                "style_presets_exists": workspace.fenjing_style_presets_root.exists(),
                "asset_registry_exists": workspace.asset_registry_path.exists(),
                "character_index_exists": workspace.character_index_path.exists(),
                "image_generation_log_exists": workspace.image_generation_log_path.exists(),
                "character_output_root_exists": episode.character_root.exists(),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "prepare":
        created = [str(path) for path in prepare_runtime_dirs(workspace)]
        task = build_episode_task(args.book_id, args.episode)
        phase2_manifest = build_phase2_episode_manifest(workspace, args.book_id, args.episode, browser=args.browser)
        phase1_manifest_path = workspace.manifests_root / "phase1-task-template.json"
        phase2_manifest_path = workspace.manifests_root / f"episode-manifest-{task['episode_id']}.json"
        phase1_manifest_path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        phase2_manifest_path.write_text(json.dumps(phase2_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    "created": created,
                    "phase1_manifest": str(phase1_manifest_path),
                    "phase2_manifest": str(phase2_manifest_path),
                    "task": task,
                    "episode_manifest": phase2_manifest,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "show-commands":
        commands = build_bridge_commands(
            workspace,
            book_id=args.book_id,
            episode_id=args.episode,
            browser=args.browser,
            asset_id=args.asset_id,
            image_path=args.image_path,
            title=args.title,
            language=args.language,
            input_path=args.input_path,
            engine_mode=args.engine_mode,
        )
        print(json.dumps(shellify(commands), ensure_ascii=False, indent=2))
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
