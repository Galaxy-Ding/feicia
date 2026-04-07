from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import AppConfig, PromptTask
from .base import BrowserOperator


class MockBrowserOperator(BrowserOperator):
    def __init__(
        self,
        *,
        login_valid: bool = True,
        page_available: bool = True,
        images_per_prompt: int = 4,
        failure_mode_by_task: Optional[Dict[str, str]] = None,
    ) -> None:
        self.login_valid = login_valid
        self.page_available = page_available
        self.images_per_prompt = images_per_prompt
        self.failure_mode_by_task = failure_mode_by_task or {}
        self.jobs: Dict[str, PromptTask] = {}

    def validate_login(self, config: AppConfig) -> bool:
        return self.login_valid and bool(config.login_markers)

    def open_generation_page(self, config: AppConfig, selectors: Dict[str, Any]) -> bool:
        return self.page_available and "elements" in selectors

    def submit_prompt(self, task: PromptTask) -> str:
        if self.failure_mode_by_task.get(task.task_id) == "submit":
            raise RuntimeError("模拟提交失败")
        job_id = f"job-{task.task_id}"
        self.jobs[job_id] = task
        return job_id

    def wait_for_generation(
        self,
        job_id: str,
        timeout_seconds: int,
        poll_interval_seconds: int,
    ) -> Dict[str, Any]:
        task = self.jobs[job_id]
        if self.failure_mode_by_task.get(task.task_id) == "wait":
            raise TimeoutError("模拟生成超时")
        return {"job_id": job_id, "status": "complete", "timeout_seconds": timeout_seconds}

    def download_images(self, task: PromptTask, staging_dir: Path) -> List[Path]:
        if self.failure_mode_by_task.get(task.task_id) == "download":
            raise RuntimeError("模拟下载失败")

        staging_dir.mkdir(parents=True, exist_ok=True)
        files: List[Path] = []
        for index in range(1, self.images_per_prompt + 1):
            path = staging_dir / f"jimeng-{task.task_id}-{index:03d}.png"
            content = f"mock-image::{task.task_id}::{index}::{task.prompt}".encode("utf-8")
            path.write_bytes(content)
            files.append(path)
        return files
