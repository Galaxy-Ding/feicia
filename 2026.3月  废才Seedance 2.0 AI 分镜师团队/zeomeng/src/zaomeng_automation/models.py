from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    LOGIN_READY = "LOGIN_READY"
    PAGE_READY = "PAGE_READY"
    PROMPT_SUBMITTED = "PROMPT_SUBMITTED"
    GENERATING = "GENERATING"
    DOWNLOAD_PENDING = "DOWNLOAD_PENDING"
    DOWNLOADED = "DOWNLOADED"
    RENAMED = "RENAMED"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    project_name: str
    jimeng_url: str
    generation_url: str
    profile_path: Path
    selectors_path: Path
    prompt_path: Path
    staging_root: Path
    images_root: Path
    run_log_dir: Path
    error_log_dir: Path
    task_state_dir: Path
    browser_state_dir: Path
    batch_id: str
    wait_timeout_seconds: int
    poll_interval_seconds: int
    download_stable_checks: int
    max_slug_length: int
    images_per_prompt: int
    openclaw_browser_profile: str = "openclaw"
    login_markers: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PromptTask:
    task_id: str
    batch: str
    prompt: str
    prompt_slug: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRecord:
    task_id: str
    batch: str
    prompt: str
    status: TaskStatus
    submitted_at: Optional[str] = None
    job_id: Optional[str] = None
    downloaded_files: List[str] = field(default_factory=list)
    last_error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class DownloadMapping:
    task_id: str
    prompt: str
    raw_filename: str
    final_filename: str
    saved_path: str
    downloaded_at: str
    index: int
    batch: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    status: str
    prompt_file: str
    processed_tasks: int
    completed_tasks: int
    failed_tasks: int
    blocked_tasks: int
    mappings_file: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
