from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def append_jsonl(log_path: Path, payload: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    enriched = {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        **payload,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(enriched, ensure_ascii=False) + "\n")
