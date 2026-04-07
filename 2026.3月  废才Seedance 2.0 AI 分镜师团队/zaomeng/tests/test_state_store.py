from __future__ import annotations

import random

from zaomeng_automation.models import TaskRecord, TaskStatus
from zaomeng_automation.state_store import TaskRepository


def test_task_repository_round_trips_three_random_cases(tmp_path) -> None:
    generator = random.Random(20260331)
    repository = TaskRepository(tmp_path)
    for index in range(3):
        record = TaskRecord(
            task_id=f"img001-{index + 1:03d}",
            batch="img001",
            prompt=f"Prompt {generator.randint(100, 999)}",
            status=TaskStatus.GENERATING,
            submitted_at="2026-03-25T14:30:00+08:00",
            job_id=f"job-{index}",
        )
        repository.save(record)
        loaded = repository.load(record.task_id)
        assert loaded.task_id == record.task_id
        assert loaded.job_id == record.job_id
        assert loaded.status == TaskStatus.GENERATING
