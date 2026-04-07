from __future__ import annotations

import argparse
import json
from pathlib import Path

from .browser.mock import MockBrowserOperator
from .browser.openclaw import OpenClawBrowserOperator
from .config import load_app_config
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
        choices=["mock", "openclaw"],
        help="浏览器适配器",
    )
    run_parser.add_argument(
        "--browser-profile",
        default=None,
        help="OpenClaw 浏览器 profile 名称，未指定时使用配置文件",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        config_path = Path(args.config)
        config = load_app_config(config_path)
        if args.browser == "mock":
            browser = MockBrowserOperator()
        else:
            browser = OpenClawBrowserOperator(
                browser_profile=args.browser_profile or config.openclaw_browser_profile,
            )
        orchestrator = RunOrchestrator(config, browser)
        summary = orchestrator.run()
        print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
