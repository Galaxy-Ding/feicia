from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


SENSITIVE_KEYS = {"password", "secret", "token", "cookie", "authorization"}


def sanitize_for_log(payload: Any) -> Any:
    if isinstance(payload, dict):
        sanitized: Dict[str, Any] = {}
        for key, value in payload.items():
            if key.lower() in SENSITIVE_KEYS:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = sanitize_for_log(value)
        return sanitized
    if isinstance(payload, list):
        return [sanitize_for_log(item) for item in payload]
    return payload


class RunLogger:
    def __init__(self, run_id: str, run_log_dir: Path, error_log_dir: Path) -> None:
        self.run_id = run_id
        self.run_log_path = run_log_dir / f"{run_id}.jsonl"
        self.error_log_path = error_log_dir / f"{run_id}.jsonl"

    def log(self, event: str, level: str = "INFO", **payload: Any) -> None:
        self._append(self.run_log_path, event=event, level=level, **payload)

    def error(self, event: str, **payload: Any) -> None:
        self._append(self.error_log_path, event=event, level="ERROR", **payload)
        self._append(self.run_log_path, event=event, level="ERROR", **payload)

    def write_summary(self, payload: Dict[str, Any]) -> Path:
        summary_path = self.run_log_path.with_name(f"{self.run_id}-summary.json")
        summary_path.write_text(
            json.dumps(sanitize_for_log(payload), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return summary_path

    def attach_diagnostic(self, name: str, content: str) -> Path:
        diagnostic_path = self.error_log_path.with_name(f"{self.run_id}-{name}.txt")
        diagnostic_path.write_text(content, encoding="utf-8")
        return diagnostic_path

    def _append(self, path: Path, event: str, level: str, **payload: Any) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "run_id": self.run_id,
            "event": event,
            "level": level,
            "payload": sanitize_for_log(payload),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
