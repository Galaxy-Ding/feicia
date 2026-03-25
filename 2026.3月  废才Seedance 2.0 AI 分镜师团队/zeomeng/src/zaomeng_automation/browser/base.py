from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from ..models import AppConfig, PromptTask


class BrowserOperator(ABC):
    @abstractmethod
    def validate_login(self, config: AppConfig) -> bool:
        raise NotImplementedError

    @abstractmethod
    def open_generation_page(self, config: AppConfig, selectors: Dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def submit_prompt(self, task: PromptTask) -> str:
        raise NotImplementedError

    @abstractmethod
    def wait_for_generation(
        self,
        job_id: str,
        timeout_seconds: int,
        poll_interval_seconds: int,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def download_images(self, task: PromptTask, staging_dir: Path) -> List[Path]:
        raise NotImplementedError
