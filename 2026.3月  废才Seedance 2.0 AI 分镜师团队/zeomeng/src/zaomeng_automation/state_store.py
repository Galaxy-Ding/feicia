from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import TaskRecord, TaskStatus


class TaskRepository:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir

    def save(self, record: TaskRecord) -> Path:
        path = self.state_dir / f"{record.task_id}.json"
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, task_id: str) -> TaskRecord:
        path = self.state_dir / f"{task_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return TaskRecord(
            task_id=payload["task_id"],
            batch=payload["batch"],
            prompt=payload["prompt"],
            status=TaskStatus(payload["status"]),
            submitted_at=payload.get("submitted_at"),
            job_id=payload.get("job_id"),
            downloaded_files=list(payload.get("downloaded_files", [])),
            last_error=payload.get("last_error"),
            retry_count=int(payload.get("retry_count", 0)),
        )

    def list_records(self) -> List[TaskRecord]:
        records = []
        for path in sorted(self.state_dir.glob("*.json")):
            records.append(self.load(path.stem))
        return records
