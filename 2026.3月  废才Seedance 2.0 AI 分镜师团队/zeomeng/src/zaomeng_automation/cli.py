from __future__ import annotations

import argparse
import json
from pathlib import Path

from .browser.mock import MockBrowserOperator
from .orchestrator import RunOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="即梦一期自动化骨架")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="执行一期流程")
    run_parser.add_argument(
        "--config",
        default="workflow/configs/project.json",
        help="配置文件路径",
    )
    run_parser.add_argument(
        "--browser",
        default="mock",
        choices=["mock"],
        help="浏览器适配器",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        browser = MockBrowserOperator()
        orchestrator = RunOrchestrator.from_path(Path(args.config), browser)
        summary = orchestrator.run()
        print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
