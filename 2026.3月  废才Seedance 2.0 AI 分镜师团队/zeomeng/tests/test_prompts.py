from __future__ import annotations

from zaomeng_automation.prompts import load_prompt_tasks


def test_load_prompt_tasks_supports_three_formats(temp_project_factory) -> None:
    cases = [
        ("sample.json", ["雨夜街头", "古风长廊", "科幻驾驶舱"]),
        ("sample.csv", ["森林薄雾", "海边逆光", "室内近景"]),
        ("sample.md", ["镜头一", "镜头二", "镜头三"]),
    ]
    for prompt_name, prompts in cases:
        _, prompt_path = temp_project_factory(prompt_name=prompt_name, prompts=prompts)
        tasks = load_prompt_tasks(prompt_path, batch="img001")
        assert [task.prompt for task in tasks] == prompts
        assert tasks[0].task_id == "img001-001"
        assert all(task.prompt_slug for task in tasks)
