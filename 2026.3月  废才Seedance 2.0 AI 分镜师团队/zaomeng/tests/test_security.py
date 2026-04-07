from __future__ import annotations

import json

import pytest

from zaomeng_automation.config import safe_join_within
from zaomeng_automation.logging_utils import sanitize_for_log


def test_safe_join_within_rejects_three_traversal_cases(tmp_path) -> None:
    cases = ["..\\evil.txt", "../evil.txt", "..\\..\\outside\\config.json"]
    for case in cases:
        with pytest.raises(ValueError):
            safe_join_within(tmp_path, case)


def test_sanitize_for_log_never_leaks_credentials() -> None:
    payload = sanitize_for_log(
        {
            "authorization": "Bearer abc",
            "nested": {"secret": "secret-value", "token": "tok-123"},
        }
    )
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "Bearer abc" not in serialized
    assert "secret-value" not in serialized
    assert "tok-123" not in serialized
