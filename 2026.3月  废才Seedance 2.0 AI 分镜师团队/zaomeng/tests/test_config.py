from __future__ import annotations

import random

from zaomeng_automation.config import load_app_config


def test_load_app_config_resolves_three_random_cases(temp_project_factory) -> None:
    generator = random.Random(20260327)
    for case_id in range(3):
        batch = f"img{generator.randint(1, 999):03d}"
        config_path, _ = temp_project_factory(
            prompt_name=f"sample-{case_id}.json",
            prompts=[f"Prompt {case_id}-{index}" for index in range(1, 4)],
            batch_id=batch,
        )
        config = load_app_config(config_path)
        assert config.batch_id == batch
        assert config.base_dir.exists()
        assert config.prompt_path.exists()
        assert config.selectors_path.exists()
        assert config.images_root.exists()
