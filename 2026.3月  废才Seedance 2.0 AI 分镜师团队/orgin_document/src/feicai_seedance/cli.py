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
