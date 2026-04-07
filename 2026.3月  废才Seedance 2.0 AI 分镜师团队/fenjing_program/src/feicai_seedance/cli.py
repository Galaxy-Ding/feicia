from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Feicai Seedance 2.0 local runner")
    parser.add_argument(
        "command",
        choices=[
            "status",
            "start",
            "design",
            "prompt",
            "extract-characters",
            "build-character-sheets",
            "export-character-image-tasks",
            "export-scene-image-tasks",
            "generate-character-images",
            "generate-scene-images",
            "review-character-images",
            "review-scene-images",
            "approve-character-assets",
            "approve-scene-assets",
            "export-character-reference-pack",
            "register-image",
            "build-reference-map",
            "revise",
            "review",
            "accept",
            "acceptance-evidence",
            "help",
        ],
    )
    parser.add_argument("episode", nargs="?")
    parser.add_argument("scope", nargs="?")
    parser.add_argument("feedback", nargs="?")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--browser", default="mock")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    pipeline = Pipeline(Path(args.project_root))

    if args.command == "status":
        print(pipeline.status_report())
    elif args.command == "start":
        print(pipeline.run_start(args.episode))
    elif args.command == "design":
        print(pipeline.run_design(args.episode))
    elif args.command == "prompt":
        print(pipeline.run_prompt(args.episode))
    elif args.command == "extract-characters":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: extract-characters <book_id> <ep01>")
        print(pipeline.run_extract_characters(args.episode, args.scope))
    elif args.command == "build-character-sheets":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: build-character-sheets <book_id> <ep01>")
        print(pipeline.run_build_character_sheets(args.episode, args.scope))
    elif args.command == "export-character-image-tasks":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: export-character-image-tasks <book_id> <ep01>")
        print(pipeline.run_export_character_image_tasks(args.episode, args.scope))
    elif args.command == "export-scene-image-tasks":
        if not args.episode:
            raise SystemExit("Usage: export-scene-image-tasks <ep01>")
        print(pipeline.run_export_scene_image_tasks(args.episode))
    elif args.command == "generate-character-images":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: generate-character-images <book_id> <ep01> [--browser mock|openclaw]")
        print(pipeline.run_generate_character_images(args.episode, args.scope, browser=args.browser))
    elif args.command == "generate-scene-images":
        if not args.episode:
            raise SystemExit("Usage: generate-scene-images <ep01> [--browser mock|openclaw]")
        print(pipeline.run_generate_scene_images(args.episode, browser=args.browser))
    elif args.command == "review-character-images":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: review-character-images <book_id> <ep01>")
        print(pipeline.run_review_character_images(args.episode, args.scope))
    elif args.command == "review-scene-images":
        if not args.episode:
            raise SystemExit("Usage: review-scene-images <ep01>")
        print(pipeline.run_review_scene_images(args.episode))
    elif args.command == "approve-character-assets":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: approve-character-assets <book_id> <ep01>")
        print(pipeline.run_approve_character_assets(args.episode, args.scope))
    elif args.command == "approve-scene-assets":
        if not args.episode:
            raise SystemExit("Usage: approve-scene-assets <ep01>")
        print(pipeline.run_approve_scene_assets(args.episode))
    elif args.command == "export-character-reference-pack":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: export-character-reference-pack <book_id> <ep01>")
        print(pipeline.run_export_character_reference_pack(args.episode, args.scope))
    elif args.command == "register-image":
        if not args.episode or not args.scope or not args.feedback:
            raise SystemExit("Usage: register-image <ep01> <asset_id> <image_path>")
        print(pipeline.run_register_image(args.episode, args.scope, args.feedback))
    elif args.command == "build-reference-map":
        if not args.episode:
            raise SystemExit("Usage: build-reference-map <ep01>")
        print(pipeline.run_build_reference_map(args.episode))
    elif args.command == "revise":
        if not args.episode or not args.scope or not args.feedback:
            raise SystemExit("Usage: revise <ep01> <director|art|storyboard> <feedback>")
        print(pipeline.run_revise(args.episode, args.scope, args.feedback))
    elif args.command == "review":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: review <ep01> <director|design|prompt|all>")
        print(pipeline.run_review(args.episode, args.scope))
    elif args.command == "accept":
        if not args.episode or not args.scope:
            raise SystemExit("Usage: accept <ep01> <director|design|prompt|all>")
        print(pipeline.run_accept(args.episode, args.scope))
    elif args.command == "acceptance-evidence":
        if not args.episode:
            raise SystemExit("Usage: acceptance-evidence <ep01>")
        print(pipeline.run_acceptance_evidence(args.episode))
    else:
        print(pipeline.command_help())


if __name__ == "__main__":
    main()
