from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .models import DownloadMapping, PromptTask
from .naming import build_final_filename


def wait_for_stable_file(path: Path, stable_checks: int = 3, interval_seconds: float = 0.05) -> bool:
    previous_size = -1
    stable_count = 0
    for _ in range(max(stable_checks * 5, stable_checks)):
        current_size = path.stat().st_size
        if current_size == previous_size:
            stable_count += 1
            if stable_count >= stable_checks:
                return True
        else:
            stable_count = 0
        previous_size = current_size
        time.sleep(interval_seconds)
    return False


def append_mapping(mapping_path: Path, mapping: DownloadMapping) -> None:
    with mapping_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(mapping.to_dict(), ensure_ascii=False) + "\n")


def archive_downloads(
    task: PromptTask,
    raw_files: Iterable[Path],
    images_root: Path,
    mapping_path: Path,
    stable_checks: int,
    max_slug_length: int,
) -> List[DownloadMapping]:
    task_output_dir = images_root / task.batch / task.task_id
    task_output_dir.mkdir(parents=True, exist_ok=True)

    mappings: List[DownloadMapping] = []
    for index, raw_file in enumerate(sorted(raw_files), start=1):
        if not wait_for_stable_file(raw_file, stable_checks=stable_checks):
            raise TimeoutError(f"Download did not stabilize: {raw_file}")

        downloaded_at = datetime.now(timezone.utc).astimezone()
        final_filename = build_final_filename(
            batch=task.batch,
            index=index,
            downloaded_at=downloaded_at,
            prompt=task.prompt,
            extension=raw_file.suffix or ".png",
            max_slug_length=max_slug_length,
        )
        final_path = task_output_dir / final_filename
        shutil.copy2(raw_file, final_path)
        mapping = DownloadMapping(
            task_id=task.task_id,
            prompt=task.prompt,
            raw_filename=raw_file.name,
            final_filename=final_filename,
            saved_path=str(final_path),
            downloaded_at=downloaded_at.isoformat(),
            index=index,
            batch=task.batch,
        )
        append_mapping(mapping_path, mapping)
        mappings.append(mapping)
    return mappings
