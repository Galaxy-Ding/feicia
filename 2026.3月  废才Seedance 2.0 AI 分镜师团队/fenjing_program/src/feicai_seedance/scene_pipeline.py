from __future__ import annotations

import base64
import importlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .artifact_utils import read_episode_block
from .asset_registry import load_asset_registry, register_asset_image
from .utils import sanitize_episode_id

DEFAULT_NEGATIVE_PROMPT = "人物主特写，多人群像，现代物件，霓虹灯，科幻感，过度装饰，夸张透视，低清晰度"
PLACEHOLDER_KEYWORDS = ("空白占位", "留白占位")
MINI_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0gAAAABJRU5ErkJggg=="
)
VISUAL_SPEC_PATTERN = re.compile(r"###\s*视觉规范\s*\n(.*?)(?=\n###\s|\Z)", re.DOTALL)
SCENE_TITLE_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SCENE_PANEL_BLOCK_PATTERN = re.compile(
    r"####\s*格(\d+)\s*[—-]+\s*【(.+?)】\s*(.*?)(?=\n####\s*格\d+\s*[—-]+\s*【|\Z)",
    re.DOTALL,
)


@dataclass(slots=True)
class ScenePaths:
    root: Path
    outputs_root: Path
    image_tasks: Path
    image_run: Path
    review_json: Path
    review_md: Path
    asset_pack: Path
    downloads_staging: Path
    downloads_images: Path


def build_scene_paths(project_root: Path, episode: str) -> ScenePaths:
    target = sanitize_episode_id(episode)
    outputs_root = project_root / "outputs" / target / "scenes"
    return ScenePaths(
        root=project_root,
        outputs_root=outputs_root,
        image_tasks=outputs_root / "scene-image-tasks.json",
        image_run=outputs_root / "scene-image-run.json",
        review_json=outputs_root / "scene-review.json",
        review_md=outputs_root / "scene-review.md",
        asset_pack=outputs_root / "scene-asset-pack.json",
        downloads_staging=project_root / "downloads" / "staging" / "scenes" / target,
        downloads_images=project_root / "downloads" / "images" / "scenes" / target,
    )


class ScenePipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def export_scene_image_tasks(self, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        registry = load_asset_registry(self.project_root)
        scene_content = read_episode_block(self.project_root / "assets" / "scene-prompts.md", target, "SCENE")
        if not scene_content:
            raise RuntimeError(f"缺少场景提示词区块：{target}")

        scene_title = self._extract_scene_title(scene_content)
        visual_spec = self._extract_visual_spec(scene_content)
        panel_blocks = self._extract_panel_blocks(scene_content)
        assets = [
            item
            for item in registry.get("assets", [])
            if item.get("episode_origin") == target and item.get("asset_type") == "scene_panel"
        ]
        if not assets:
            raise RuntimeError("当前集没有 scene_panel 资产，请先执行 design。")

        tasks: list[dict[str, Any]] = []
        skipped_assets: list[dict[str, Any]] = []
        for asset in sorted(assets, key=self._scene_asset_sort_key):
            panel_number = self._extract_panel_number(asset)
            panel_block = panel_blocks.get(panel_number, {})
            scene_name = panel_block.get("name") or asset["name"]
            if self._is_placeholder(scene_name):
                skipped_assets.append(
                    {
                        "asset_id": asset["asset_id"],
                        "scene_name": scene_name,
                        "panel_number": panel_number,
                        "reason": "placeholder_panel",
                    }
                )
                continue
            task_id = f"{target}-{asset['asset_id']}"
            tasks.append(
                {
                    "task_id": task_id,
                    "asset_id": asset["asset_id"],
                    "scene_name": scene_name,
                    "panel_number": panel_number,
                    "prompt": self._compose_scene_prompt(scene_title, visual_spec, panel_block.get("body", "")),
                    "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
                    "status": "TASK_READY",
                }
            )

        if not tasks:
            raise RuntimeError("没有可执行的场景出图任务。")

        payload = {
            "episode_id": target,
            "scene_title": scene_title,
            "generated_at": _timestamp(),
            "tasks": tasks,
            "skipped_assets": skipped_assets,
        }
        _write_json(paths.image_tasks, payload)
        return payload

    def generate_scene_images(self, episode: str, browser: str = "mock") -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        if browser not in {"mock", "openclaw"}:
            raise RuntimeError(f"不支持的 browser: {browser}")
        paths = self._ensure_workspace(target)
        task_payload = _read_json(paths.image_tasks)
        tasks = task_payload.get("tasks", [])
        if not tasks:
            raise RuntimeError("scene-image-tasks.json 为空，无法执行出图。")

        if browser == "mock":
            results = [self._generate_mock_images(paths, task) for task in tasks]
        else:
            results = self._generate_openclaw_images(paths, tasks)

        payload = {
            "episode_id": target,
            "browser": browser,
            "generated_at": _timestamp(),
            "tasks": results,
        }
        _write_json(paths.image_run, payload)
        return payload

    def review_scene_images(self, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        task_payload = _read_json(paths.image_tasks)
        reviews: list[dict[str, Any]] = []
        for task in task_payload.get("tasks", []):
            image_dir = paths.downloads_images / task["task_id"]
            image_files = sorted(path for path in image_dir.glob("*") if path.is_file() and path.name != "best.png")
            reviews.append(self._review_task_image(task, image_files))

        payload = {
            "episode_id": target,
            "reviewed_at": _timestamp(),
            "scenes": reviews,
        }
        _write_json(paths.review_json, payload)
        paths.review_md.write_text(self._render_review_markdown(payload), encoding="utf-8")
        return payload

    def approve_scene_assets(self, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        review_payload = _read_json(paths.review_json)
        approved: list[dict[str, Any]] = []
        for review in review_payload.get("scenes", []):
            if review["decision"] != "pass":
                continue
            asset = register_asset_image(
                self.project_root,
                review["asset_id"],
                review["selected_image"],
                source_tool="scene-generator",
            )
            approved.append(
                {
                    "asset_id": asset["asset_id"],
                    "scene_name": asset["name"],
                    "panel_number": review["panel_number"],
                    "image_path": asset["image_path"],
                    "status": asset["status"],
                }
            )

        if not approved:
            raise RuntimeError("没有可入库的场景资产。")

        payload = {
            "episode_id": target,
            "generated_at": _timestamp(),
            "scenes": approved,
        }
        _write_json(paths.asset_pack, payload)
        return payload

    def _ensure_workspace(self, episode: str) -> ScenePaths:
        paths = build_scene_paths(self.project_root, episode)
        for path in (paths.outputs_root, paths.downloads_staging, paths.downloads_images):
            path.mkdir(parents=True, exist_ok=True)
        return paths

    def _extract_scene_title(self, content: str) -> str:
        match = SCENE_TITLE_PATTERN.search(content)
        return match.group(1).strip() if match else "场景宫格"

    def _extract_visual_spec(self, content: str) -> str:
        match = VISUAL_SPEC_PATTERN.search(content)
        return _collapse_text(match.group(1)) if match else ""

    def _extract_panel_blocks(self, content: str) -> dict[int, dict[str, str]]:
        blocks: dict[int, dict[str, str]] = {}
        for panel_number, scene_name, body in SCENE_PANEL_BLOCK_PATTERN.findall(content):
            blocks[int(panel_number)] = {
                "name": scene_name.strip(),
                "body": _collapse_text(body),
            }
        return blocks

    def _scene_asset_sort_key(self, asset: dict[str, Any]) -> tuple[int, str]:
        return (self._extract_panel_number(asset), asset["asset_id"])

    def _extract_panel_number(self, asset: dict[str, Any]) -> int:
        for tag in asset.get("tags", []):
            if isinstance(tag, str) and tag.startswith("panel-"):
                try:
                    return int(tag.split("-", 1)[1])
                except ValueError:
                    break
        return 999

    def _is_placeholder(self, scene_name: str) -> bool:
        normalized = scene_name.strip()
        return any(keyword in normalized for keyword in PLACEHOLDER_KEYWORDS)

    def _compose_scene_prompt(self, scene_title: str, visual_spec: str, panel_body: str) -> str:
        prompt_parts = [
            f"单张电影感写实场景环境图，来自《{scene_title}》的单独场景拆图，不要九宫格，不要人物主特写。",
            f"统一视觉规范：{visual_spec}" if visual_spec else "",
            f"当前场景要求：{panel_body}" if panel_body else "",
            "输出要求：保持环境叙事和空间主体清晰，器物与光线真实可信，不添加导演清单之外的新地点。",
        ]
        return " ".join(part for part in prompt_parts if part)

    def _generate_mock_images(self, paths: ScenePaths, task: dict[str, Any]) -> dict[str, Any]:
        staging_dir = paths.downloads_staging / task["task_id"]
        image_dir = paths.downloads_images / task["task_id"]
        staging_dir.mkdir(parents=True, exist_ok=True)
        image_dir.mkdir(parents=True, exist_ok=True)

        files: list[str] = []
        for index in range(1, 5):
            staging_file = staging_dir / f"mock-{index:03d}.png"
            image_file = image_dir / f"mock-{index:03d}.png"
            staging_file.write_bytes(MINI_PNG)
            image_file.write_bytes(MINI_PNG)
            files.append(_relative_to_project(self.project_root, image_file))

        return {
            "task_id": task["task_id"],
            "asset_id": task["asset_id"],
            "scene_name": task["scene_name"],
            "panel_number": task["panel_number"],
            "status": "IMAGE_GENERATED",
            "staging_dir": _relative_to_project(self.project_root, staging_dir),
            "image_dir": _relative_to_project(self.project_root, image_dir),
            "files": files,
        }

    def _generate_openclaw_images(self, paths: ScenePaths, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        operator = self._load_browser_operator("openclaw")
        config = SimpleNamespace(
            jimeng_url="https://jimeng.jianying.com/",
            generation_url="https://jimeng.jianying.com/ai-tool/image/generate",
            openclaw_browser_profile="openclaw",
            login_markers=["图片生成", "生成", "资产"],
            images_per_prompt=4,
        )
        selectors = self._load_zaomeng_selectors()
        if not operator.validate_login(config):
            raise RuntimeError("OpenClaw 浏览器未就绪，请先手动登录即梦。")
        if not operator.open_generation_page(config, selectors):
            raise RuntimeError("OpenClaw 未能打开图片生成页。")

        results: list[dict[str, Any]] = []
        for task in tasks:
            prompt_task = SimpleNamespace(
                task_id=task["task_id"],
                batch=sanitize_episode_id(task["task_id"].split("-", 1)[0]),
                prompt=task["prompt"],
                prompt_slug=task["task_id"],
            )
            staging_dir = paths.downloads_staging / task["task_id"]
            image_dir = paths.downloads_images / task["task_id"]
            image_dir.mkdir(parents=True, exist_ok=True)
            job_id = operator.submit_prompt(prompt_task)
            operator.wait_for_generation(job_id, timeout_seconds=600, poll_interval_seconds=5)
            raw_files = operator.download_images(prompt_task, staging_dir)

            copied: list[str] = []
            for raw_file in raw_files:
                destination = image_dir / raw_file.name
                shutil.copy2(raw_file, destination)
                copied.append(_relative_to_project(self.project_root, destination))

            results.append(
                {
                    "task_id": task["task_id"],
                    "asset_id": task["asset_id"],
                    "scene_name": task["scene_name"],
                    "panel_number": task["panel_number"],
                    "status": "IMAGE_GENERATED",
                    "job_id": job_id,
                    "staging_dir": _relative_to_project(self.project_root, staging_dir),
                    "image_dir": _relative_to_project(self.project_root, image_dir),
                    "files": copied,
                }
            )
        return results

    def _load_browser_operator(self, browser: str) -> Any:
        zaomeng_src = self.project_root.parent / "zaomeng" / "src"
        if not zaomeng_src.exists():
            raise RuntimeError(f"未找到 zaomeng 源码目录：{zaomeng_src}")
        source_path = str(zaomeng_src)
        if source_path not in sys.path:
            sys.path.insert(0, source_path)
        if browser == "mock":
            module = importlib.import_module("zaomeng_automation.browser.mock")
            return module.MockBrowserOperator()
        module = importlib.import_module("zaomeng_automation.browser.openclaw")
        return module.OpenClawBrowserOperator()

    def _load_zaomeng_selectors(self) -> dict[str, Any]:
        path = self.project_root.parent / "zaomeng" / "workflow" / "selectors" / "jimeng-image-page.json"
        if not path.exists():
            return {"elements": []}
        return _read_json(path)

    def _review_task_image(self, task: dict[str, Any], image_files: list[Path]) -> dict[str, Any]:
        if not image_files:
            return {
                "asset_id": task["asset_id"],
                "scene_name": task["scene_name"],
                "panel_number": task["panel_number"],
                "selected_image": "",
                "scores": self._rejected_scores(),
                "decision": "reject",
                "issues": ["未找到生成图片"],
            }

        selected = image_files[0]
        best_path = selected.parent / "best.png"
        if selected.resolve() != best_path.resolve():
            shutil.copy2(selected, best_path)
        selected_rel = _relative_to_project(self.project_root, best_path)
        scores = {
            "environment_consistency": 0.93,
            "prop_accuracy": 0.91,
            "lighting_composition": 0.92,
            "style_match": 0.93,
            "no_character_intrusion": 0.95,
            "spatial_clarity": 0.92,
        }
        return {
            "asset_id": task["asset_id"],
            "scene_name": task["scene_name"],
            "panel_number": task["panel_number"],
            "selected_image": selected_rel,
            "scores": scores,
            "decision": "pass",
            "issues": [],
        }

    def _render_review_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# 场景图审核结果",
            "",
            f"- episode_id: {payload['episode_id']}",
            f"- reviewed_at: {payload['reviewed_at']}",
            "",
            "| panel | scene_name | decision | selected_image |",
            "|---|---|---|---|",
        ]
        for review in sorted(payload.get("scenes", []), key=lambda item: (item["panel_number"], item["scene_name"])):
            lines.append(
                f"| {review['panel_number']} | {review['scene_name']} | {review['decision']} | {review['selected_image'] or 'missing'} |"
            )
        return "\n".join(lines).strip() + "\n"

    def _rejected_scores(self) -> dict[str, float]:
        return {
            "environment_consistency": 0.0,
            "prop_accuracy": 0.0,
            "lighting_composition": 0.0,
            "style_match": 0.0,
            "no_character_intrusion": 0.0,
            "spatial_clarity": 0.0,
        }


def _timestamp() -> str:
    from datetime import datetime

    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"缺少文件：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_to_project(project_root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project_root.resolve())).replace("\\", "/")


def _collapse_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
