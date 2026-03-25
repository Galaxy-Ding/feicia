from __future__ import annotations

import re
from pathlib import Path

from .structured_protocols import parse_director_markdown, parse_seedance_markdown


def split_art_design_artifact(artifact: str) -> tuple[str, str]:
    character_header = "# 人物提示词"
    scene_header = "# 场景道具提示词"

    char_start = artifact.find(character_header)
    scene_start = artifact.find(scene_header)
    if char_start == -1 or scene_start == -1:
        raise ValueError("阶段二输出缺少人物或场景标题，无法拆分。")
    if scene_start < char_start:
        raise ValueError("阶段二输出结构错误，场景部分出现在人物部分之前。")

    character_part = artifact[char_start:scene_start].strip() + "\n"
    scene_part = artifact[scene_start:].strip() + "\n"
    return character_part, scene_part


def append_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8").strip():
        existing = path.read_text(encoding="utf-8").rstrip() + "\n\n---\n\n" + content.strip() + "\n"
        path.write_text(existing, encoding="utf-8")
        return
    path.write_text(content.strip() + "\n", encoding="utf-8")


def upsert_episode_block(path: Path, episode: str, block_name: str, content: str) -> None:
    start = f"<!-- BEGIN {block_name}:{episode} -->"
    end = f"<!-- END {block_name}:{episode} -->"
    wrapped = f"{start}\n{content.strip()}\n{end}\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(wrapped, encoding="utf-8")
        return

    existing = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"<!-- BEGIN {re.escape(block_name)}:{re.escape(episode)} -->.*?<!-- END {re.escape(block_name)}:{re.escape(episode)} -->\n?",
        re.DOTALL,
    )
    if pattern.search(existing):
        updated = pattern.sub(wrapped, existing)
    else:
        updated = existing.rstrip() + "\n\n" + wrapped
    path.write_text(updated.strip() + "\n", encoding="utf-8")


def read_episode_block(path: Path, episode: str, block_name: str) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"<!-- BEGIN {re.escape(block_name)}:{re.escape(episode)} -->\n(.*?)\n<!-- END {re.escape(block_name)}:{re.escape(episode)} -->",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def has_episode_block(path: Path, episode: str, block_name: str) -> bool:
    return bool(read_episode_block(path, episode, block_name))


def validate_director_artifact(text: str) -> None:
    required = ["# 导演讲戏本", "## 人物清单", "## 场景清单"]
    _assert_required_sections(text, required, "阶段一")
    parse_director_markdown("ep00", text)


def validate_character_asset(text: str) -> None:
    required = ["# 人物提示词", "**出图要求**", "**提示词**"]
    _assert_required_sections(text, required, "人物资产")


def validate_scene_asset(text: str) -> None:
    required = ["# 场景道具提示词", "### 视觉规范", "### Panel Breakdown"]
    _assert_required_sections(text, required, "场景资产")


def validate_seedance_artifact(text: str) -> None:
    required = ["## 素材对应表", "**Seedance 2.0 提示词**"]
    _assert_required_sections(text, required, "阶段三")
    parse_seedance_markdown("ep00", text)


def _assert_required_sections(text: str, required: list[str], label: str) -> None:
    missing = [item for item in required if item not in text]
    if missing:
        joined = "、".join(missing)
        raise ValueError(f"{label}输出缺少必要结构：{joined}")
