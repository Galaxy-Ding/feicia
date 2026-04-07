from __future__ import annotations

import random
import string
from datetime import datetime, timedelta, timezone

from zaomeng_automation.naming import build_final_filename, make_task_id, slugify_prompt


def test_slugify_prompt_handles_three_random_cases() -> None:
    generator = random.Random(20260325)
    for _ in range(3):
        prompt = "".join(generator.choice(string.ascii_letters + string.digits + " ./_中文-!?") for _ in range(40))
        slug = slugify_prompt(prompt, max_length=20)
        assert slug
        assert len(slug) <= 20
        assert "/" not in slug
        assert "\\" not in slug
        assert slug == slug.lower()


def test_make_task_id_and_filename_handle_three_random_cases() -> None:
    generator = random.Random(20260326)
    base_time = datetime(2026, 3, 25, 14, 30, tzinfo=timezone.utc).astimezone()
    for ordinal in range(1, 4):
        batch = f"img{generator.randint(1, 999):03d}"
        prompt = f"Rainy street {generator.randint(100, 999)}"
        task_id = make_task_id(batch, ordinal)
        filename = build_final_filename(batch, ordinal, base_time + timedelta(minutes=ordinal), prompt, extension=".png")
        assert task_id.endswith(f"{ordinal:03d}")
        assert filename.startswith(f"{batch}_{ordinal:03d}_")
        assert filename.endswith(".png")
        assert "rainy-street" in filename
