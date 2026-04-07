from __future__ import annotations

import json
import random

from zaomeng_automation.logging_utils import RunLogger, sanitize_for_log


def test_sanitize_for_log_redacts_three_random_cases() -> None:
    generator = random.Random(20260330)
    for _ in range(3):
        payload = {
            "token": f"tok-{generator.randint(1000, 9999)}",
            "cookie": f"cookie-{generator.randint(1000, 9999)}",
            "nested": {"password": f"pw-{generator.randint(1000, 9999)}"},
        }
        sanitized = sanitize_for_log(payload)
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["cookie"] == "***REDACTED***"
        assert sanitized["nested"]["password"] == "***REDACTED***"


def test_run_logger_writes_sanitized_output(tmp_path) -> None:
    logger = RunLogger("run-001", tmp_path, tmp_path)
    logger.log("task.started", token="secret-token", task_id="img001-001")
    logger.write_summary({"status": "COMPLETED", "password": "abc"})
    log_entry = json.loads((tmp_path / "run-001.jsonl").read_text(encoding="utf-8").splitlines()[0])
    summary = json.loads((tmp_path / "run-001-summary.json").read_text(encoding="utf-8"))
    assert log_entry["payload"]["token"] == "***REDACTED***"
    assert summary["password"] == "***REDACTED***"
