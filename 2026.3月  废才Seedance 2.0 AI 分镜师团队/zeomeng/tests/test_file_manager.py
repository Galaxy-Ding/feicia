from __future__ import annotations

import random
from pathlib import Path

from zaomeng_automation.file_manager import archive_downloads, wait_for_stable_file
from zaomeng_automation.models import PromptTask


def test_wait_for_stable_file_accepts_three_random_cases(tmp_path: Path) -> None:
    generator = random.Random(20260328)
    for index in range(3):
        file_path = tmp_path / f"stable-{index}.png"
        file_path.write_bytes(f"payload-{generator.randint(1000, 9999)}".encode("utf-8"))
        assert wait_for_stable_file(file_path, stable_checks=1, interval_seconds=0.001) is True


def test_archive_downloads_creates_three_random_mappings(tmp_path: Path) -> None:
    generator = random.Random(20260329)
    images_root = tmp_path / "images"
    mapping_path = tmp_path / "mappings.jsonl"
    for case_id in range(3):
        task = PromptTask(
            task_id=f"img001-{case_id + 1:03d}",
            batch="img001",
            prompt=f"Prompt {generator.randint(100, 999)} cinematic street",
            prompt_slug="prompt",
        )
        raw_files = []
        for raw_index in range(2):
            raw_file = tmp_path / f"raw-{case_id}-{raw_index}.png"
            raw_file.write_bytes(b"mock")
            raw_files.append(raw_file)
        mappings = archive_downloads(task, raw_files, images_root, mapping_path, stable_checks=1, max_slug_length=24)
        assert len(mappings) == 2
        assert all(Path(mapping.saved_path).exists() for mapping in mappings)
        assert all(mapping.final_filename.endswith(".png") for mapping in mappings)
