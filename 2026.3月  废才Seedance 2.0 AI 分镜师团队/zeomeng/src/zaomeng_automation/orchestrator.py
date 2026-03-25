from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .browser.base import BrowserOperator
from .config import load_app_config
from .file_manager import archive_downloads
from .logging_utils import RunLogger
from .models import AppConfig, RunSummary, TaskRecord, TaskStatus
from .prompts import load_prompt_tasks
from .state_store import TaskRepository


class RunOrchestrator:
    def __init__(self, config: AppConfig, browser: BrowserOperator) -> None:
        self.config = config
        self.browser = browser
        self.task_repository = TaskRepository(config.task_state_dir)

    @classmethod
    def from_path(cls, config_path: Path, browser: BrowserOperator) -> "RunOrchestrator":
        return cls(load_app_config(config_path), browser)

    def run(self, prompt_path: Optional[Path] = None) -> RunSummary:
        run_id = datetime.now(timezone.utc).astimezone().strftime("run-%Y%m%dT%H%M%S")
        logger = RunLogger(run_id, self.config.run_log_dir, self.config.error_log_dir)
        selectors = self._load_selectors()
        task_file = prompt_path or self.config.prompt_path
        tasks = load_prompt_tasks(task_file, batch=self.config.batch_id, max_slug_length=self.config.max_slug_length)
        mappings_path = self.config.images_root / self.config.batch_id / f"{run_id}-mapping.jsonl"
        mappings_path.parent.mkdir(parents=True, exist_ok=True)

        logger.log("run.started", config_path=str(task_file), task_count=len(tasks))

        if not self.browser.validate_login(self.config):
            logger.error("login.blocked", reason="登录态无效或缺少登录标识")
            summary = RunSummary(
                run_id=run_id,
                status=TaskStatus.BLOCKED.value,
                prompt_file=str(task_file),
                processed_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                blocked_tasks=len(tasks),
                mappings_file=str(mappings_path),
            )
            logger.write_summary(summary.to_dict())
            return summary

        if not self.browser.open_generation_page(self.config, selectors):
            logger.error("page.failed", reason="图片页选择器未命中")
            summary = RunSummary(
                run_id=run_id,
                status=TaskStatus.FAILED.value,
                prompt_file=str(task_file),
                processed_tasks=0,
                completed_tasks=0,
                failed_tasks=len(tasks),
                blocked_tasks=0,
                mappings_file=str(mappings_path),
            )
            logger.write_summary(summary.to_dict())
            return summary

        completed = 0
        failed = 0
        for task in tasks:
            record = TaskRecord(task_id=task.task_id, batch=task.batch, prompt=task.prompt, status=TaskStatus.PENDING)
            try:
                self._transition(record, TaskStatus.LOGIN_READY, logger)
                self._transition(record, TaskStatus.PAGE_READY, logger)

                record.submitted_at = datetime.now(timezone.utc).astimezone().isoformat()
                record.job_id = self.browser.submit_prompt(task)
                self._transition(record, TaskStatus.PROMPT_SUBMITTED, logger, job_id=record.job_id)
                self._transition(record, TaskStatus.GENERATING, logger)

                self.browser.wait_for_generation(
                    record.job_id,
                    timeout_seconds=self.config.wait_timeout_seconds,
                    poll_interval_seconds=self.config.poll_interval_seconds,
                )
                self._transition(record, TaskStatus.DOWNLOAD_PENDING, logger)

                staging_dir = self.config.staging_root / task.task_id
                raw_files = self.browser.download_images(task, staging_dir)
                record.downloaded_files = [path.name for path in raw_files]
                self._transition(record, TaskStatus.DOWNLOADED, logger, raw_files=record.downloaded_files)

                mappings = archive_downloads(
                    task=task,
                    raw_files=raw_files,
                    images_root=self.config.images_root,
                    mapping_path=mappings_path,
                    stable_checks=self.config.download_stable_checks,
                    max_slug_length=self.config.max_slug_length,
                )
                record.downloaded_files = [mapping.final_filename for mapping in mappings]
                self._transition(record, TaskStatus.RENAMED, logger, files=record.downloaded_files)
                self._transition(record, TaskStatus.COMPLETED, logger)
                completed += 1
            except Exception as exc:  # pragma: no cover - exercised via tests
                record.last_error = str(exc)
                record.retry_count += 1
                record.status = TaskStatus.FAILED
                self.task_repository.save(record)
                logger.error("task.failed", task_id=task.task_id, error=str(exc))
                logger.attach_diagnostic(task.task_id, f"task={task.task_id}\nerror={exc}\nprompt={task.prompt}")
                failed += 1

        summary = RunSummary(
            run_id=run_id,
            status=TaskStatus.COMPLETED.value if failed == 0 else TaskStatus.FAILED.value,
            prompt_file=str(task_file),
            processed_tasks=len(tasks),
            completed_tasks=completed,
            failed_tasks=failed,
            blocked_tasks=0,
            mappings_file=str(mappings_path),
        )
        logger.write_summary(summary.to_dict())
        logger.log("run.completed", **summary.to_dict())
        return summary

    def _load_selectors(self) -> Dict[str, Any]:
        with self.config.selectors_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _transition(self, record: TaskRecord, status: TaskStatus, logger: RunLogger, **payload: Any) -> None:
        record.status = status
        self.task_repository.save(record)
        logger.log("task.status", task_id=record.task_id, status=status.value, **payload)
