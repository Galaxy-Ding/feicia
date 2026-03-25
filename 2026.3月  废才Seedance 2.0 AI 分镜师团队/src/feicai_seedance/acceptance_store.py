from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

STAGES = ("director", "design", "prompt")


def load_acceptance_state(reports_root: Path, episode: str) -> dict[str, Any]:
    path = _acceptance_path(reports_root, episode)
    if not path.exists():
        return {
            "episode": episode,
            "stages": {stage: {"status": "not_started"} for stage in STAGES},
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_stage_acceptance(
    reports_root: Path,
    episode: str,
    stage: str,
    status: str,
    source: str,
    summary: dict[str, Any] | None = None,
    notes: str | None = None,
) -> Path:
    state = load_acceptance_state(reports_root, episode)
    state.setdefault("stages", {})
    state["stages"][stage] = {
        "status": status,
        "source": source,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "summary": summary or {},
        "notes": notes or "",
    }
    path = _acceptance_path(reports_root, episode)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def get_stage_status(reports_root: Path, episode: str, stage: str) -> str:
    state = load_acceptance_state(reports_root, episode)
    return state.get("stages", {}).get(stage, {}).get("status", "not_started")


def _acceptance_path(reports_root: Path, episode: str) -> Path:
    return reports_root / "acceptance" / f"{episode}.json"
