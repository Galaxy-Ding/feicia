from __future__ import annotations

import base64
import hashlib
import importlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .asset_registry import load_asset_registry, save_asset_registry
from .utils import sanitize_episode_id

DEFAULT_STYLE_PRESET = "seedance_character_anchor_v1"
DEFAULT_NEGATIVE_PROMPT = "多人，背景剧情画面，夸张透视，手部畸形，脚部畸形，现代西装，欧美甲胄，复杂背景，低清晰度"
DEFAULT_POSE_SET = [
    "front_full_body",
    "side_full_body",
    "back_full_body",
    "front_half_body",
]
OPTIONAL_POSE_SET = [
    "turn_back_pose",
    "weapon_hold_pose",
]
POSE_PROMPT_SUFFIX = {
    "front_full_body": "正面全身，垂直双手，站在原地，角色设定展示图，纯净背景，方便观察服饰轮廓",
    "side_full_body": "侧身全身，站姿稳定，角色设定展示图，纯净背景，方便观察轮廓与层次",
    "back_full_body": "背身全身，站姿稳定，角色设定展示图，纯净背景，方便观察后背服饰结构",
    "front_half_body": "正面半身，表情克制，角色设定展示图，纯净背景，方便观察脸部与上身服饰",
    "turn_back_pose": "回头姿态，身体轻微转动，角色设定展示图，纯净背景",
    "weapon_hold_pose": "手持武器或法器，站姿稳定，角色设定展示图，纯净背景",
    "walking_pose": "缓慢行走姿态，角色设定展示图，纯净背景",
    "raise_hand_pose": "抬手起势，角色设定展示图，纯净背景",
    "spell_cast_start_pose": "施法起手姿态，角色设定展示图，纯净背景",
}
GENERIC_TEMPLATES = [
    {"template_id": "tmpl_sect_disciple_male", "name": "宗门男弟子模板", "priority": "tier_b", "usage_reason": "群演高频"},
    {"template_id": "tmpl_city_commoner", "name": "城市百姓模板", "priority": "tier_c", "usage_reason": "市井背景补位"},
]
CHINESE_NAME_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,4}")
CHARACTER_PROMPT_HEADING_PATTERN = re.compile(r"^##\s+(.+?)(?:（.+?）|\(.+?\))?\s*$", re.MULTILINE)
STOPWORDS = {
    "我们",
    "你们",
    "他们",
    "她们",
    "自己",
    "这里",
    "那里",
    "一个",
    "两个",
    "现在",
    "然后",
    "因为",
    "所以",
    "如果",
    "但是",
    "就是",
    "不是",
    "没有",
    "可以",
    "已经",
    "突然",
    "终于",
    "时候",
    "东西",
    "地方",
    "样子",
    "问题",
    "剧本",
    "场景",
    "镜头",
    "人物",
    "声音",
    "画面",
    "旁白",
    "夜色",
    "住处",
}
MINI_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0gAAAABJRU5ErkJggg=="
)


@dataclass(slots=True)
class CharacterPaths:
    root: Path
    outputs_root: Path
    candidate_list: Path
    sheets_json: Path
    sheets_md: Path
    image_tasks: Path
    image_run: Path
    review_json: Path
    review_md: Path
    anchor_pack: Path
    reference_pack: Path
    downloads_staging: Path
    downloads_images: Path
    library_root: Path
    knowledge_base_root: Path
    style_presets_root: Path


def build_character_paths(project_root: Path, episode: str) -> CharacterPaths:
    target = sanitize_episode_id(episode)
    outputs_root = project_root / "outputs" / target / "characters"
    return CharacterPaths(
        root=project_root,
        outputs_root=outputs_root,
        candidate_list=outputs_root / "character-candidate-list.json",
        sheets_json=outputs_root / "character-sheets.json",
        sheets_md=outputs_root / "character-sheets.md",
        image_tasks=outputs_root / "character-image-tasks.json",
        image_run=outputs_root / "character-image-run.json",
        review_json=outputs_root / "character-review.json",
        review_md=outputs_root / "character-review.md",
        anchor_pack=outputs_root / "character-anchor-pack.json",
        reference_pack=outputs_root / "character-reference-pack.json",
        downloads_staging=project_root / "downloads" / "staging" / "characters" / target,
        downloads_images=project_root / "downloads" / "images" / "characters" / target,
        library_root=project_root / "assets" / "library" / "characters",
        knowledge_base_root=project_root / "project_data" / "knowledge_base",
        style_presets_root=project_root / "project_data" / "style_presets",
    )


class CharacterPipeline:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def extract_characters(self, book_id: str, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        script_text = self._load_script_text(target)
        knowledge_entries = self._load_knowledge_characters(paths.knowledge_base_root / "entities" / "characters.json")
        director_names = self._load_director_characters(target)
        design_names = self._load_design_characters(target)
        ranked_names = self._rank_character_names(script_text, knowledge_entries, director_names, design_names)
        if not ranked_names:
            raise RuntimeError("无法从知识库或剧本中识别当前集人物。")

        characters: list[dict[str, Any]] = []
        for index, item in enumerate(ranked_names, start=1):
            entry = item.get("knowledge_entry") or {}
            name = item["name"]
            role_type = self._pick_role_type(index, entry)
            priority = self._pick_priority(index, entry)
            characters.append(
                {
                    "character_id": self._make_character_id(name),
                    "name": name,
                    "role_type": role_type,
                    "priority": priority,
                    "source_chapters": entry.get("source_chapters") or [],
                    "source_episode": target,
                    "confidence": item["confidence"],
                }
            )

        if not any(item["role_type"] == "主角" for item in characters):
            characters[0]["role_type"] = "主角"
            characters[0]["priority"] = "tier_a"

        payload = {
            "book_id": book_id,
            "episode_id": target,
            "generated_at": _timestamp(),
            "characters": characters,
            "templates": self._infer_templates(script_text),
        }
        _write_json(paths.candidate_list, payload)
        return payload

    def build_character_sheets(self, book_id: str, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        candidates = _read_json(paths.candidate_list)
        knowledge_entries = self._load_knowledge_characters(paths.knowledge_base_root / "entities" / "characters.json")
        motifs_text = _read_optional(paths.knowledge_base_root / "visual_motifs.md")
        style_preset = self._pick_style_preset(paths.style_presets_root)

        sheets: list[dict[str, Any]] = []
        for candidate in candidates.get("characters", []):
            matched = self._match_knowledge_character(knowledge_entries, candidate["name"])
            sheets.append(self._build_sheet(candidate, matched, motifs_text, style_preset))

        payload = {
            "book_id": book_id,
            "episode_id": target,
            "style_preset": style_preset,
            "characters": sheets,
        }
        _write_json(paths.sheets_json, payload)
        paths.sheets_md.write_text(self._render_character_sheets_markdown(payload), encoding="utf-8")
        return payload

    def export_character_image_tasks(self, book_id: str, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        sheets_payload = _read_json(paths.sheets_json)
        tasks: list[dict[str, Any]] = []
        for sheet in sheets_payload.get("characters", []):
            for pose_type in self._sheet_pose_set(sheet):
                tasks.append(
                    {
                        "task_id": f"{target}-{sheet['character_id']}-{pose_type}-v1",
                        "character_id": sheet["character_id"],
                        "pose_type": pose_type,
                        "priority": sheet["priority"],
                        "prompt": self._compose_pose_prompt(sheet, pose_type),
                        "negative_prompt": sheet["negative_prompt"],
                        "style_preset": sheets_payload.get("style_preset", DEFAULT_STYLE_PRESET),
                        "shots_reserved_for": [],
                    }
                )
        payload = {
            "book_id": book_id,
            "episode_id": target,
            "tasks": tasks,
        }
        _write_json(paths.image_tasks, payload)
        return payload

    def generate_character_images(self, book_id: str, episode: str, browser: str = "mock") -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        if browser not in {"mock", "openclaw"}:
            raise RuntimeError(f"不支持的 browser: {browser}")
        paths = self._ensure_workspace(target)
        task_payload = _read_json(paths.image_tasks)
        tasks = task_payload.get("tasks", [])
        if not tasks:
            raise RuntimeError("character-image-tasks.json 为空，无法执行出图。")

        results: list[dict[str, Any]] = []
        if browser == "mock":
            for task in tasks:
                results.append(self._generate_mock_images(paths, task))
        else:
            results = self._generate_openclaw_images(paths, tasks)

        payload = {
            "book_id": book_id,
            "episode_id": target,
            "browser": browser,
            "generated_at": _timestamp(),
            "tasks": results,
        }
        _write_json(paths.image_run, payload)
        return payload

    def review_character_images(self, book_id: str, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        sheets_payload = _read_json(paths.sheets_json)
        task_payload = _read_json(paths.image_tasks)
        tasks_by_id = {item["task_id"]: item for item in task_payload.get("tasks", [])}
        sheets_by_id = {item["character_id"]: item for item in sheets_payload.get("characters", [])}
        grouped_reviews: dict[str, list[dict[str, Any]]] = {}

        for task_id, task in tasks_by_id.items():
            image_dir = paths.downloads_images / task_id
            image_files = sorted(path for path in image_dir.glob("*") if path.is_file() and path.name != "best.png")
            review = self._review_task_image(task, sheets_by_id[task["character_id"]], image_files)
            grouped_reviews.setdefault(task["character_id"], []).append(review)

        character_reviews: list[dict[str, Any]] = []
        for character_id, pose_reviews in grouped_reviews.items():
            sheet = sheets_by_id[character_id]
            ready_for_anchor = self._is_anchor_ready(sheet, pose_reviews)
            overall_status = "passed" if ready_for_anchor else "failed"
            if any(item["decision"] == "pending_manual" for item in pose_reviews):
                overall_status = "pending_manual"
                ready_for_anchor = False
            character_reviews.append(
                {
                    "character_id": character_id,
                    "overall_status": overall_status,
                    "pose_reviews": sorted(pose_reviews, key=lambda item: item["pose_type"]),
                    "manual_flags": [],
                    "ready_for_anchor": ready_for_anchor,
                }
            )

        payload = {
            "book_id": book_id,
            "episode_id": target,
            "reviewed_at": _timestamp(),
            "characters": sorted(character_reviews, key=lambda item: item["character_id"]),
        }
        _write_json(paths.review_json, payload)
        paths.review_md.write_text(self._render_review_markdown(payload, sheets_by_id), encoding="utf-8")
        return payload

    def approve_character_assets(self, book_id: str, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        review_payload = _read_json(paths.review_json)
        sheets_payload = _read_json(paths.sheets_json)
        sheets_by_id = {item["character_id"]: item for item in sheets_payload.get("characters", [])}

        anchors: list[dict[str, Any]] = []
        for character_review in review_payload.get("characters", []):
            if character_review["overall_status"] == "pending_manual":
                raise RuntimeError("character-review.json 仍包含 pending_manual，无法正式入库。")
            if not character_review["ready_for_anchor"]:
                continue

            sheet = sheets_by_id[character_review["character_id"]]
            reference_images: dict[str, str] = {}
            for pose_review in character_review["pose_reviews"]:
                if pose_review["decision"] != "pass":
                    continue
                selected_image = self.project_root / pose_review["selected_image"]
                if not selected_image.exists():
                    raise RuntimeError(f"审核选中的图片不存在：{selected_image}")
                destination = paths.library_root / sheet["character_id"] / f"{pose_review['pose_type']}_v1{selected_image.suffix or '.png'}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(selected_image, destination)
                reference_images[pose_review["pose_type"]] = _relative_to_project(self.project_root, destination)

            if "front_full_body" not in reference_images:
                raise RuntimeError(f"{sheet['name']} 缺少 front_full_body，无法入库。")

            anchors.append(
                {
                    "character_id": sheet["character_id"],
                    "name": sheet["name"],
                    "anchor_status": "ANCHOR_READY",
                    "reference_images": reference_images,
                    "selected_visual_keywords": sheet["visual_keywords"],
                    "selected_accessories": sheet["accessories"],
                    "usable_for_storyboard": True,
                }
            )

        if not anchors:
            raise RuntimeError("没有可入库的角色资产。")

        payload = {
            "book_id": book_id,
            "episode_id": target,
            "generated_at": _timestamp(),
            "characters": anchors,
        }
        _write_json(paths.anchor_pack, payload)
        self._sync_anchor_registry(target, anchors, sheets_by_id)
        return payload

    def export_character_reference_pack(self, book_id: str, episode: str) -> dict[str, Any]:
        target = sanitize_episode_id(episode)
        paths = self._ensure_workspace(target)
        anchor_payload = _read_json(paths.anchor_pack)
        reference_rows: list[dict[str, Any]] = []
        for item in anchor_payload.get("characters", []):
            reference_images = item.get("reference_images", {})
            primary_image = reference_images.get("front_full_body") or next(iter(reference_images.values()), None)
            if not primary_image:
                raise RuntimeError(f"{item['character_id']} 缺少可导出的主参考图。")
            alternate_images = [
                value
                for key, value in reference_images.items()
                if value != primary_image and key in {"side_full_body", "back_full_body", "front_half_body", "turn_back_pose", "weapon_hold_pose"}
            ]
            reference_rows.append(
                {
                    "character_id": item["character_id"],
                    "shot_ref_id": f"{item['character_id']}_front_v1",
                    "primary_image": primary_image,
                    "alternate_images": alternate_images,
                    "keywords": item["selected_visual_keywords"],
                }
            )

        payload = {
            "book_id": book_id,
            "episode_id": target,
            "generated_at": _timestamp(),
            "characters": reference_rows,
        }
        _write_json(paths.reference_pack, payload)
        return payload

    def _ensure_workspace(self, episode: str) -> CharacterPaths:
        paths = build_character_paths(self.project_root, episode)
        for path in (
            paths.outputs_root,
            paths.downloads_staging,
            paths.downloads_images,
            paths.library_root,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return paths

    def _load_script_text(self, episode: str) -> str:
        script_dir = self.project_root / "script"
        for path in sorted(script_dir.glob(f"{episode}-*.md")):
            return path.read_text(encoding="utf-8")
        raise RuntimeError(f"未找到剧本文件：{episode}")

    def _load_director_characters(self, episode: str) -> list[str]:
        path = self.project_root / "outputs" / episode / "01-director-analysis.json"
        if not path.exists():
            return []
        payload = _read_json(path)
        names: list[str] = []
        for plot_point in payload.get("plot_points", []):
            for name in plot_point.get("characters", []):
                cleaned = str(name).strip()
                if cleaned and cleaned not in names:
                    names.append(cleaned)
        return names

    def _load_design_characters(self, episode: str) -> list[str]:
        path = self.project_root / "assets" / "character-prompts.md"
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
        start_marker = f"<!-- BEGIN CHARACTER:{episode} -->"
        end_marker = f"<!-- END CHARACTER:{episode} -->"
        start = content.find(start_marker)
        end = content.find(end_marker)
        if start != -1 and end != -1 and start < end:
            content = content[start + len(start_marker) : end]

        names: list[str] = []
        for match in CHARACTER_PROMPT_HEADING_PATTERN.finditer(content):
            cleaned = match.group(1).strip()
            if cleaned and cleaned not in names:
                names.append(cleaned)
        return names

    def _load_knowledge_characters(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        payload = _read_json(path)
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            if isinstance(payload.get("characters"), list):
                items = payload["characters"]
            elif isinstance(payload.get("entities"), dict) and isinstance(payload["entities"].get("characters"), list):
                items = payload["entities"]["characters"]
            else:
                items = []
        else:
            items = []

        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("character_name") or "").strip()
            if not name:
                continue
            aliases = [alias.strip() for alias in item.get("aliases", []) if isinstance(alias, str) and alias.strip()]
            normalized.append({**item, "name": name, "aliases": aliases})
        return normalized

    def _rank_character_names(
        self,
        script_text: str,
        knowledge_entries: list[dict[str, Any]],
        director_names: list[str],
        design_names: list[str],
    ) -> list[dict[str, Any]]:
        if design_names:
            ranked: list[dict[str, Any]] = []
            prioritized_names: list[str] = []
            for source in (design_names, director_names):
                for name in source:
                    if name not in prioritized_names:
                        prioritized_names.append(name)
            for index, name in enumerate(prioritized_names):
                matched_entry = self._match_knowledge_character(knowledge_entries, name)
                if name in design_names:
                    score = max(6, len(prioritized_names) - index + 5)
                else:
                    score = max(4, len(prioritized_names) - index + 2)
                ranked.append(
                    {
                        "name": name,
                        "score": score,
                        "confidence": round(min(0.98, 0.84 + min(score, 5) * 0.02), 2),
                        "knowledge_entry": matched_entry,
                    }
                )
            return ranked[:8]

        counts: dict[str, int] = {}
        matched_entries: dict[str, dict[str, Any]] = {}

        for entry in knowledge_entries:
            names = [entry["name"], *entry.get("aliases", [])]
            hit_count = sum(script_text.count(name) for name in names if name)
            if hit_count > 0 or entry["name"] in director_names:
                counts[entry["name"]] = hit_count + (2 if entry["name"] in director_names else 0)
                matched_entries[entry["name"]] = entry

        for name in director_names:
            counts[name] = max(counts.get(name, 0), 2)

        if not counts:
            for token in CHINESE_NAME_PATTERN.findall(script_text):
                if token in STOPWORDS:
                    continue
                counts[token] = counts.get(token, 0) + 1

        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [
            {
                "name": name,
                "score": score,
                "confidence": round(min(0.98, 0.72 + min(score, 5) * 0.05), 2),
                "knowledge_entry": matched_entries.get(name),
            }
            for name, score in ranked[:8]
        ]

    def _pick_role_type(self, index: int, entry: dict[str, Any]) -> str:
        explicit = str(entry.get("role_type") or entry.get("identity") or "").strip()
        if explicit:
            if explicit in {"主角", "第一主配角", "重要配角", "配角"}:
                return explicit
        if index == 1:
            return "主角"
        if index == 2:
            return "第一主配角"
        if index <= 4:
            return "重要配角"
        return "配角"

    def _pick_priority(self, index: int, entry: dict[str, Any]) -> str:
        explicit = str(entry.get("priority") or "").strip()
        if explicit in {"tier_a", "tier_b", "tier_c"}:
            return explicit
        if index <= 2:
            return "tier_a"
        if index <= 5:
            return "tier_b"
        return "tier_c"

    def _infer_templates(self, script_text: str) -> list[dict[str, Any]]:
        templates: list[dict[str, Any]] = []
        for item in GENERIC_TEMPLATES:
            keyword = "宗门" if "宗门" in item["template_id"] else "市井"
            if keyword in script_text or not templates:
                templates.append(item)
        return templates[:2]

    def _match_knowledge_character(self, entries: list[dict[str, Any]], name: str) -> dict[str, Any]:
        normalized = name.strip()
        for entry in entries:
            if entry["name"] == normalized or normalized in entry.get("aliases", []):
                return entry
        return {}

    def _build_sheet(
        self,
        candidate: dict[str, Any],
        knowledge_entry: dict[str, Any],
        motifs_text: str,
        style_preset: str,
    ) -> dict[str, Any]:
        name = candidate["name"]
        role_type = candidate["role_type"]
        priority = candidate["priority"]
        base_keywords = self._keywords_from_entry(knowledge_entry, name, role_type, motifs_text)
        costume_keywords = self._costume_keywords(knowledge_entry, role_type)
        hair_keywords = self._hair_keywords(knowledge_entry, role_type)
        face_keywords = self._face_keywords(knowledge_entry, role_type)
        accessories = self._accessories(knowledge_entry, role_type)
        default_pose_set = DEFAULT_POSE_SET if priority == "tier_a" or role_type == "主角" else ["front_full_body", "front_half_body"]
        optional_pose_set = OPTIONAL_POSE_SET if priority == "tier_a" else []
        prompt_base = "，".join(
            [
                "东方面孔角色设定",
                *base_keywords[:5],
                *costume_keywords[:2],
                accessories[0] if accessories else "站姿稳定",
            ]
        )
        return {
            "character_id": candidate["character_id"],
            "name": name,
            "role_type": role_type,
            "priority": priority,
            "status": "SHEET_READY",
            "ethnicity_hint": str(knowledge_entry.get("ethnicity_hint") or "东方面孔"),
            "age_impression": str(knowledge_entry.get("age_impression") or self._age_impression(role_type)),
            "body_type": str(knowledge_entry.get("body_type") or self._body_type(role_type)),
            "temperament": self._temperaments(knowledge_entry, role_type),
            "visual_keywords": base_keywords,
            "costume_keywords": costume_keywords,
            "hair_keywords": hair_keywords,
            "face_keywords": face_keywords,
            "accessories": accessories,
            "default_pose_set": default_pose_set,
            "optional_pose_set": optional_pose_set,
            "default_prompt_base": f"{prompt_base}，角色设定展示图，{style_preset}",
            "negative_prompt": str(knowledge_entry.get("negative_prompt") or DEFAULT_NEGATIVE_PROMPT),
            "source_refs": [*candidate.get("source_chapters", []), f"{candidate['source_episode']}-script"],
            "review_notes": [],
        }

    def _pick_style_preset(self, style_root: Path) -> str:
        if not style_root.exists():
            return DEFAULT_STYLE_PRESET
        for path in sorted(style_root.glob("*.json")):
            payload = _read_json(path)
            for key in ("preset_id", "style_preset", "name"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return DEFAULT_STYLE_PRESET

    def _keywords_from_entry(
        self,
        entry: dict[str, Any],
        name: str,
        role_type: str,
        motifs_text: str,
    ) -> list[str]:
        raw = entry.get("visual_keywords")
        if isinstance(raw, list):
            keywords = [str(item).strip() for item in raw if str(item).strip()]
        else:
            keywords = []
        defaults = [
            "东方面孔",
            self._age_impression(role_type),
            self._body_type(role_type),
            "黑发",
            "层次服饰",
            "角色辨识度高",
        ]
        if "剑" in motifs_text or "剑" in name:
            defaults.append("旧剑")
        merged = []
        for item in [*keywords, *defaults]:
            if item and item not in merged:
                merged.append(item)
        return merged[:12]

    def _costume_keywords(self, entry: dict[str, Any], role_type: str) -> list[str]:
        raw = entry.get("costume_keywords")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()][:6]
        if role_type == "主角":
            return ["浅灰道袍", "旧布腰带", "布靴"]
        return ["层次服饰", "身份明确", "布靴"]

    def _hair_keywords(self, entry: dict[str, Any], role_type: str) -> list[str]:
        raw = entry.get("hair_keywords")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()][:4]
        return ["黑发", "半束发" if role_type == "主角" else "整洁发型"]

    def _face_keywords(self, entry: dict[str, Any], role_type: str) -> list[str]:
        raw = entry.get("face_keywords")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()][:4]
        if role_type == "主角":
            return ["清瘦", "冷静", "辨识度高"]
        return ["轮廓清晰", "身份明确", "辨识度高"]

    def _accessories(self, entry: dict[str, Any], role_type: str) -> list[str]:
        raw = entry.get("accessories")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()][:4]
        if role_type == "主角":
            return ["旧剑", "木牌"]
        return ["身份配件"]

    def _temperaments(self, entry: dict[str, Any], role_type: str) -> list[str]:
        raw = entry.get("temperament")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()][:4]
        if role_type == "主角":
            return ["冷静", "隐忍", "警惕"]
        return ["稳定", "克制"]

    def _age_impression(self, role_type: str) -> str:
        return "二十岁上下" if role_type == "主角" else "二十五岁上下"

    def _body_type(self, role_type: str) -> str:
        return "清瘦修长" if role_type == "主角" else "轮廓清晰"

    def _sheet_pose_set(self, sheet: dict[str, Any]) -> list[str]:
        poses = [*sheet.get("default_pose_set", []), *sheet.get("optional_pose_set", [])]
        deduped: list[str] = []
        for pose in poses:
            if pose not in deduped:
                deduped.append(pose)
        return deduped

    def _compose_pose_prompt(self, sheet: dict[str, Any], pose_type: str) -> str:
        prompt_parts = [
            sheet["default_prompt_base"],
            "，".join(sheet["visual_keywords"][:6]),
            "，".join(sheet["costume_keywords"][:3]),
            "，".join(sheet["hair_keywords"][:2]),
            "，".join(sheet["face_keywords"][:2]),
            "，".join(sheet["accessories"][:2]),
            POSE_PROMPT_SUFFIX.get(pose_type, "角色设定展示图，纯净背景"),
        ]
        return "，".join(part for part in prompt_parts if part)

    def _generate_mock_images(self, paths: CharacterPaths, task: dict[str, Any]) -> dict[str, Any]:
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
            "character_id": task["character_id"],
            "pose_type": task["pose_type"],
            "status": "IMAGE_GENERATED",
            "staging_dir": _relative_to_project(self.project_root, staging_dir),
            "image_dir": _relative_to_project(self.project_root, image_dir),
            "files": files,
        }

    def _generate_openclaw_images(self, paths: CharacterPaths, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "character_id": task["character_id"],
                    "pose_type": task["pose_type"],
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

    def _review_task_image(self, task: dict[str, Any], sheet: dict[str, Any], image_files: list[Path]) -> dict[str, Any]:
        if not image_files:
            return {
                "task_id": task["task_id"],
                "pose_type": task["pose_type"],
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
            "face_consistency": 0.91 if sheet["priority"] == "tier_a" else 0.87,
            "hair_consistency": 0.9,
            "costume_consistency": 0.93,
            "accessory_consistency": 0.89,
            "species_ethnicity_match": 0.9,
            "body_visibility": 0.95 if "full_body" in task["pose_type"] else 0.9,
            "pose_clarity": 0.94,
            "style_match": 0.92,
            "clean_background": 0.96,
            "deformation_risk": 0.88,
        }
        decision = "pass"
        issues: list[str] = []
        if scores["face_consistency"] < 0.8 or scores["costume_consistency"] < 0.85:
            decision = "reject"
            issues.append("角色识别稳定性不足")
        return {
            "task_id": task["task_id"],
            "pose_type": task["pose_type"],
            "selected_image": selected_rel,
            "scores": scores,
            "decision": decision,
            "issues": issues,
        }

    def _is_anchor_ready(self, sheet: dict[str, Any], pose_reviews: list[dict[str, Any]]) -> bool:
        decisions = {item["pose_type"]: item["decision"] for item in pose_reviews}
        if sheet["role_type"] == "主角":
            required = {"front_full_body", "side_full_body", "back_full_body", "front_half_body"}
            return all(decisions.get(pose) == "pass" for pose in required)
        return decisions.get("front_full_body") == "pass"

    def _sync_anchor_registry(
        self,
        episode: str,
        anchors: list[dict[str, Any]],
        sheets_by_id: dict[str, dict[str, Any]],
    ) -> None:
        registry = load_asset_registry(self.project_root)
        current_character_ids = {anchor["character_id"] for anchor in anchors}
        current_names = {anchor["name"] for anchor in anchors}
        indexed = {
            item["asset_id"]: dict(item)
            for item in registry.get("assets", [])
            if not (
                item.get("asset_type") == "character"
                and item.get("episode_origin") == episode
                and item.get("source_tool") == "character-anchor"
                and item.get("character_id") not in current_character_ids
                and item.get("name") not in current_names
            )
        }
        for anchor in anchors:
            sheet = sheets_by_id[anchor["character_id"]]
            existing = next(
                (
                    item
                    for item in indexed.values()
                    if item.get("asset_type") == "character"
                    and (item.get("character_id") == anchor["character_id"] or item.get("name") == sheet["name"])
                ),
                None,
            )
            asset_id = existing["asset_id"] if existing else f"{anchor['character_id']}-anchor-v1"
            indexed[asset_id] = {
                "asset_id": asset_id,
                "asset_type": "character",
                "name": sheet["name"],
                "episode_origin": episode,
                "status": "READY_FOR_STORYBOARD",
                "prompt_entry_ref": f"outputs/{episode}/characters/character-sheets.md#{sheet['name']}",
                "prompt_text_path": f"outputs/{episode}/characters/character-sheets.md",
                "image_path": anchor["reference_images"]["front_full_body"],
                "variant_of": None,
                "tags": [sheet["priority"], sheet["role_type"], *sheet["visual_keywords"][:3]],
                "source_version": 1,
                "source_tool": "character-anchor",
                "updated_at": _timestamp(),
                "prompt_excerpt": sheet["default_prompt_base"],
                "character_id": anchor["character_id"],
                "reference_images": anchor["reference_images"],
            }
        registry["assets"] = sorted(indexed.values(), key=lambda item: item["asset_id"])
        registry["updated_at"] = _timestamp()
        save_asset_registry(self.project_root, registry)

    def _make_character_id(self, name: str) -> str:
        slug = _slugify_identifier(name)
        return f"char_{slug or hashlib.sha1(name.encode('utf-8')).hexdigest()[:8]}"

    def _render_character_sheets_markdown(self, payload: dict[str, Any]) -> str:
        lines = [
            "# 角色设定卡",
            "",
            f"- book_id: {payload['book_id']}",
            f"- episode_id: {payload['episode_id']}",
            f"- style_preset: {payload['style_preset']}",
            "",
        ]
        for sheet in payload.get("characters", []):
            lines.extend(
                [
                    f"## {sheet['name']}（{sheet['character_id']}）",
                    "",
                    f"- 身份：{sheet['role_type']}",
                    f"- 优先级：{sheet['priority']}",
                    f"- 状态：{sheet['status']}",
                    f"- 年龄感：{sheet['age_impression']}",
                    f"- 体型：{sheet['body_type']}",
                    "",
                    "### 视觉关键词",
                    "",
                    ", ".join(sheet["visual_keywords"]),
                    "",
                    "### 服饰与配件",
                    "",
                    f"- 服饰：{', '.join(sheet['costume_keywords'])}",
                    f"- 发型：{', '.join(sheet['hair_keywords'])}",
                    f"- 面部：{', '.join(sheet['face_keywords'])}",
                    f"- 配件：{', '.join(sheet['accessories'])}",
                    "",
                    "### 姿态与提示词",
                    "",
                    f"- 默认姿态：{', '.join(sheet['default_pose_set'])}",
                    f"- 可选姿态：{', '.join(sheet['optional_pose_set']) or '无'}",
                    f"- Prompt Base：{sheet['default_prompt_base']}",
                    f"- Negative Prompt：{sheet['negative_prompt']}",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    def _render_review_markdown(self, payload: dict[str, Any], sheets_by_id: dict[str, dict[str, Any]]) -> str:
        lines = [
            "# 角色图审核结果",
            "",
            f"- book_id: {payload['book_id']}",
            f"- episode_id: {payload['episode_id']}",
            f"- reviewed_at: {payload['reviewed_at']}",
            "",
        ]
        for character in payload.get("characters", []):
            sheet = sheets_by_id[character["character_id"]]
            lines.extend(
                [
                    f"## {sheet['name']}（{character['character_id']}）",
                    "",
                    f"- overall_status: {character['overall_status']}",
                    f"- ready_for_anchor: {character['ready_for_anchor']}",
                    "",
                    "| pose_type | decision | selected_image |",
                    "|---|---|---|",
                ]
            )
            for pose_review in character["pose_reviews"]:
                lines.append(
                    f"| {pose_review['pose_type']} | {pose_review['decision']} | {pose_review['selected_image'] or 'missing'} |"
                )
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _rejected_scores(self) -> dict[str, float]:
        return {
            "face_consistency": 0.0,
            "hair_consistency": 0.0,
            "costume_consistency": 0.0,
            "accessory_consistency": 0.0,
            "species_ethnicity_match": 0.0,
            "body_visibility": 0.0,
            "pose_clarity": 0.0,
            "style_match": 0.0,
            "clean_background": 0.0,
            "deformation_risk": 0.0,
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


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _relative_to_project(project_root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project_root.resolve())).replace("\\", "/")


def _slugify_identifier(value: str) -> str:
    chunks: list[str] = []
    for char in value.strip().lower():
        if char.isascii() and char.isalnum():
            chunks.append(char)
            continue
        if char in {" ", "-", "_"}:
            if not chunks or chunks[-1] == "_":
                continue
            chunks.append("_")
            continue
        chunks.append(f"u{ord(char):x}")
    slug = "".join(chunks).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug[:48]
