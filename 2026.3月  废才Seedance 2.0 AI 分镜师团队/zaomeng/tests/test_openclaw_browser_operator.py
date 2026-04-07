from __future__ import annotations

from pathlib import Path

from zaomeng_automation.browser.openclaw import OpenClawBrowserOperator
from zaomeng_automation.models import PromptTask


LOGIN_SNAPSHOT = """
- generic [ref=e2]:
  - menuitem "登录" [ref=e52] [cursor=pointer]:
    - generic [ref=e54]: 登录
""".strip()

ENTRY_SNAPSHOT = """
- generic [ref=e2]:
  - menuitem "图片生成" [ref=e23] [cursor=pointer]:
    - generic [ref=e30]: 图片生成
""".strip()

GENERATION_SNAPSHOT = """
- generic [ref=e2]:
  - textbox [ref=e118]:
    - paragraph [ref=e119]: 输入文字
  - button "生成" [ref=e151] [cursor=pointer]:
    - generic [ref=e152]: 生成
""".strip()

DOWNLOAD_SNAPSHOT = """
- generic [ref=e2]:
  - button "下载" [ref=e201] [cursor=pointer]:
    - generic [ref=e202]: 下载
  - button "下载" [ref=e203] [cursor=pointer]:
    - generic [ref=e204]: 下载
""".strip()


class FakeOpenClawRunner:
    def __init__(self, *, temp_download_root: Path) -> None:
        self.temp_download_root = temp_download_root
        self.commands: list[list[str]] = []
        self.snapshots = [ENTRY_SNAPSHOT, GENERATION_SNAPSHOT, GENERATION_SNAPSHOT, DOWNLOAD_SNAPSHOT]
        self.current_url = "https://jimeng.jianying.com/"

    def __call__(self, command: list[str]) -> str:
        self.commands.append(command)
        args = command[4:]
        action = args[0]

        if action == "start":
            return "browser running"
        if action == "open":
            self.current_url = args[1]
            return f"opened: {self.current_url}\nid: TARGET123"
        if action == "focus":
            return f"focused tab {args[1]}"
        if action == "navigate":
            self.current_url = args[1]
            return f"navigated to {self.current_url}"
        if action == "wait":
            return "wait complete"
        if action == "tabs":
            return ""
        if action == "evaluate":
            if "--fn" in args and "() => location.href" in args:
                return f'"{self.current_url}"'
            return "true"
        if action == "snapshot":
            if self.snapshots:
                return self.snapshots.pop(0)
            return DOWNLOAD_SNAPSHOT
        if action == "type":
            return f"typed into ref {args[1]}"
        if action == "click":
            return f"clicked ref {args[1]}"
        if action == "press":
            return f"pressed {args[1]}"
        if action == "download":
            target_path = Path(args[2])
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(b"fake-image")
            return f"saved: {target_path}"
        raise AssertionError(f"Unexpected command: {command}")


def test_validate_login_returns_false_when_login_entry_is_visible(temp_project_factory, tmp_path: Path) -> None:
    config_path, _ = temp_project_factory(prompt_name="sample.json", prompts=["镜头一"])
    runner = FakeOpenClawRunner(temp_download_root=tmp_path / "downloads")
    runner.snapshots = [LOGIN_SNAPSHOT]
    operator = OpenClawBrowserOperator(
        browser_profile="openclaw",
        openclaw_bin=Path("/tmp/openclaw"),
        command_runner=runner,
    )

    config = operator.config if operator.config else None
    if config is None:
        from zaomeng_automation.config import load_app_config

        config = load_app_config(config_path)

    assert operator.validate_login(config) is False


def test_open_generation_page_clicks_entry_and_detects_prompt_input(temp_project_factory, tmp_path: Path) -> None:
    config_path, _ = temp_project_factory(prompt_name="sample.json", prompts=["镜头一"])
    runner = FakeOpenClawRunner(temp_download_root=tmp_path / "downloads")
    operator = OpenClawBrowserOperator(
        browser_profile="openclaw",
        openclaw_bin=Path("/tmp/openclaw"),
        command_runner=runner,
    )

    from zaomeng_automation.config import load_app_config

    config = load_app_config(config_path)
    selectors = {
        "elements": [
            {"name": "image_generation_entry", "match_text": "图片生成"},
            {"name": "prompt_input", "primary_selector": "textarea[placeholder*='提示词']"},
            {"name": "generate_button", "match_text": "生成"},
        ]
    }

    assert operator.open_generation_page(config, selectors) is True
    assert any(command[4:6] == ["click", "e23"] for command in runner.commands)


def test_submit_wait_and_download_complete_real_operator_flow(temp_project_factory, tmp_path: Path) -> None:
    config_path, _ = temp_project_factory(prompt_name="sample.json", prompts=["镜头一"])
    runner = FakeOpenClawRunner(temp_download_root=tmp_path / "downloads")
    operator = OpenClawBrowserOperator(
        browser_profile="openclaw",
        openclaw_bin=Path("/tmp/openclaw"),
        command_runner=runner,
        sleep_fn=lambda _: None,
    )

    from zaomeng_automation.config import load_app_config

    config = load_app_config(config_path)
    runner.snapshots = [GENERATION_SNAPSHOT, GENERATION_SNAPSHOT, DOWNLOAD_SNAPSHOT]
    operator.config = config
    operator.selectors = {
        "elements": [
            {"name": "prompt_input", "primary_selector": "textarea[placeholder*='提示词']"},
            {"name": "generate_button", "match_text": "生成"},
        ]
    }
    operator.target_id = "TARGET123"

    task = PromptTask(task_id="img001-001", batch="img001", prompt="雨夜街头", prompt_slug="雨夜街头")
    job_id = operator.submit_prompt(task)
    result = operator.wait_for_generation(job_id, timeout_seconds=1, poll_interval_seconds=0)
    files = operator.download_images(task, tmp_path / "staging")

    assert job_id.startswith("openclaw-img001-001-")
    assert result["status"] == "complete"
    assert len(files) == 2
    assert all(path.exists() for path in files)
    assert any(command[4:6] == ["evaluate", "--ref"] and command[6] == "e118" for command in runner.commands)
    assert any(command[4:6] == ["click", "e151"] for command in runner.commands)


def test_wait_and_download_fallback_to_result_image_urls(
    temp_project_factory,
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_path, _ = temp_project_factory(prompt_name="sample.json", prompts=["镜头一"])
    runner = FakeOpenClawRunner(temp_download_root=tmp_path / "downloads")
    runner.snapshots = [GENERATION_SNAPSHOT, GENERATION_SNAPSHOT]
    operator = OpenClawBrowserOperator(
        browser_profile="openclaw",
        openclaw_bin=Path("/tmp/openclaw"),
        command_runner=runner,
        sleep_fn=lambda _: None,
    )

    from zaomeng_automation.config import load_app_config

    config = load_app_config(config_path)
    operator.config = config
    operator.target_id = "TARGET123"
    operator.previous_result_urls = {"https://cdn.example.com/old.webp"}
    monkeypatch.setattr(operator, "_expected_image_count", lambda: 1)

    image_url_calls = iter(
        [
            ["https://cdn.example.com/old.webp"],
            ["https://cdn.example.com/new.webp"],
            ["https://cdn.example.com/new.webp"],
        ]
    )
    monkeypatch.setattr(
        operator,
        "_collect_result_image_urls",
        lambda limit: next(image_url_calls, ["https://cdn.example.com/new.webp"]),
    )
    monkeypatch.setattr(operator, "_open_result_view", lambda snapshot: True)

    downloaded: list[tuple[str, Path]] = []

    def fake_download(url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"fake-image")
        downloaded.append((url, destination))

    monkeypatch.setattr(operator, "_download_image_from_url", fake_download)

    task = PromptTask(task_id="img001-001", batch="img001", prompt="雨夜街头", prompt_slug="雨夜街头")
    result = operator.wait_for_generation("job-1", timeout_seconds=1, poll_interval_seconds=0)
    files = operator.download_images(task, tmp_path / "staging")

    assert result["status"] == "complete"
    assert operator.ready_result_urls == ["https://cdn.example.com/new.webp"]
    assert [item[0] for item in downloaded] == ["https://cdn.example.com/new.webp"]
    assert len(files) == 1
    assert files[0].suffix == ".webp"
    assert files[0].exists()
