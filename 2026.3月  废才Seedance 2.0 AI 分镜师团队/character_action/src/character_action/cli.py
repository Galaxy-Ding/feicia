from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import CharacterActionPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Character Action CLI")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--config", default="configs/dev.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare")
    subparsers.add_parser("doctor")

    preprocess = subparsers.add_parser("preprocess-book")
    preprocess.add_argument("--book-id", required=True)
    preprocess.add_argument("--title", required=True)
    preprocess.add_argument("--language", required=True, choices=["zh", "en"])
    preprocess.add_argument("--input", required=True)
    preprocess.add_argument("--author", default="")
    preprocess.add_argument("--engine-mode", choices=["auto", "native", "fallback"])

    extract = subparsers.add_parser("extract-characters")
    extract.add_argument("--book-id", required=True)

    extract_llm = subparsers.add_parser("extract-characters-llm")
    extract_llm.add_argument("--book-id", required=True)
    extract_llm.add_argument("--llm-config")
    extract_llm.add_argument("--extractor-provider", default="codex")
    extract_llm.add_argument("--extractor-model", default="gpt-5.4")
    extract_llm.add_argument("--reviewer-provider", default="claude")
    extract_llm.add_argument("--reviewer-model", default="gpt-5.4")

    relations = subparsers.add_parser("build-relations")
    relations.add_argument("--book-id", required=True)

    qa = subparsers.add_parser("run-qa")
    qa.add_argument("--book-id", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--book-id")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline = CharacterActionPipeline(Path(args.project_root), args.config)
    if args.command == "prepare":
        print(json.dumps(pipeline.prepare(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "doctor":
        print(json.dumps(pipeline.doctor(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "preprocess-book":
        print(
            json.dumps(
                pipeline.preprocess_book(
                    book_id=args.book_id,
                    title=args.title,
                    language=args.language,
                    input_path=args.input,
                    author=args.author,
                    engine_mode=args.engine_mode,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "extract-characters":
        print(json.dumps(pipeline.extract_characters(book_id=args.book_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "extract-characters-llm":
        print(
            json.dumps(
                pipeline.extract_characters_llm(
                    book_id=args.book_id,
                    llm_config_path=args.llm_config,
                    extractor_provider=args.extractor_provider,
                    extractor_model=args.extractor_model,
                    reviewer_provider=args.reviewer_provider,
                    reviewer_model=args.reviewer_model,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "build-relations":
        print(json.dumps(pipeline.build_relations(book_id=args.book_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "run-qa":
        print(json.dumps(pipeline.run_qa(book_id=args.book_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "status":
        print(json.dumps(pipeline.status(args.book_id), ensure_ascii=False, indent=2))
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
