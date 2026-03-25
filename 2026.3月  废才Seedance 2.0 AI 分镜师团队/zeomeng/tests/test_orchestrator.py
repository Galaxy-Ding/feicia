from __future__ import annotations

import json
from pathlib import Path

from zaomeng_automation.browser.mock import MockBrowserOperator
from zaomeng_automation.orchestrator import RunOrchestrator


def test_mock_pipeline_runs_end_to_end(temp_project_factory) -> None:
    config_path, _ = temp_project_factory(
        prompt_name="sample.json",
        prompts=["雨夜街头", "古风长廊", "科幻驾驶舱"],
    )
    summary = RunOrchestrator.from_path(config_path, MockBrowserOperator()).run()
    assert summary.status == "COMPLETED"
    assert summary.processed_tasks == 3
    assert summary.completed_tasks == 3

    mapping_lines = Path(summary.mappings_file).read_text(encoding="utf-8").splitlines()
    assert len(mapping_lines) == 12
    first_mapping = json.loads(mapping_lines[0])
    assert first_mapping["task_id"] == "img001-001"


def test_mock_pipeline_records_task_failures(temp_project_factory) -> None:
    config_path, _ = temp_project_factory(
        prompt_name="sample.json",
        prompts=["镜头一", "镜头二", "镜头三"],
    )
    browser = MockBrowserOperator(failure_mode_by_task={"img001-002": "download"})
    summary = RunOrchestrator.from_path(config_path, browser).run()
    assert summary.status == "FAILED"
    assert summary.completed_tasks == 2
    assert summary.failed_tasks == 1
