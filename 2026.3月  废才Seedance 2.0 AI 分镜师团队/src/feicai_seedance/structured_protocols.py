from __future__ import annotations

import json
import re
from datetime import datetime
import math
from pathlib import Path
from typing import Any

from .models import ReviewOutcome
from .utils import choose_grid_spec

ABSTRACT_WORDS = ("悲伤", "孤独", "疲惫", "紧张", "忧郁", "压抑", "绝望", "焦虑")
ACTION_HINTS = ("走", "跑", "冲", "坐", "站", "抬", "推", "拉", "转", "摸", "看", "听", "翻", "拿", "抓", "按", "喊", "进入", "离开", "揉")
CAMERA_HINTS = ("镜头", "推近", "拉远", "摇镜", "移动镜头", "跟拍", "升镜", "降镜", "俯拍", "仰拍", "左移", "右移", "前移", "后移")
LIGHT_HINTS = ("台灯", "顶灯", "窗", "窗外", "月光", "阳光", "霓虹", "火光", "逆光", "侧光", "背光", "顶光", "冷白", "暖黄")
AUDIO_HINTS = ("声音", "音效", "呼吸", "脚步", "风声", "雨声", "环境音", "音乐", "对白", "纸页", "摩擦声")
SAFE_ZONE_HEAD_HINTS = ("开场立刻", "一开场就", "第一秒", "刚开始就")
SAFE_ZONE_TAIL_HINTS = ("最后一秒", "最后半秒", "结尾立刻", "尾声突然")
REFERENCE_PATTERN = re.compile(r"@图片\d+")
PLOT_HEADING_PATTERN = re.compile(r"^##\s+(P\d+)\s+(.+)$", re.MULTILINE)
TABLE_ROW_PATTERN = re.compile(r"^\|(.+)\|$")
SENTENCE_SPLIT_PATTERN = re.compile(r"[。！？!?]+")


def ensure_asset_registry_files(assets_root: Path) -> None:
    registry_dir = assets_root / "registry"
    library_dir = assets_root / "library"
    manifests_dir = assets_root / "manifests"
    for path in (
        registry_dir,
        library_dir / "characters",
        library_dir / "scenes",
        library_dir / "scene-panels",
        manifests_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)

    registry_files = {
        registry_dir / "asset-registry.json": {
            "version": "1.0",
            "updated_at": _timestamp(),
            "assets": [],
        },
        registry_dir / "character-index.json": {
            "version": "1.0",
            "updated_at": _timestamp(),
            "characters": [],
        },
        registry_dir / "scene-index.json": {
            "version": "1.0",
            "updated_at": _timestamp(),
            "scenes": [],
        },
    }
    for path, payload in registry_files.items():
        if not path.exists():
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path = manifests_dir / "image-generation-log.jsonl"
    if not manifest_path.exists():
        manifest_path.write_text("", encoding="utf-8")


def parse_director_markdown(episode: str, text: str) -> dict[str, Any]:
    plot_section = text.split("## 人物清单", 1)[0]
    plot_points: list[dict[str, Any]] = []
    matches = list(PLOT_HEADING_PATTERN.finditer(plot_section))
    for index, match in enumerate(matches):
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(plot_section)
        block = plot_section[match.start() : block_end].strip()
        plot_id = match.group(1).strip()
        title = match.group(2).strip()
        characters = _split_inline_values(_extract_labeled_value(block, "人物"))
        scenes = _split_inline_values(_extract_labeled_value(block, "场景"))
        shot_group_type = _extract_labeled_value(block, "镜头组") or "unknown"
        duration_seconds = _extract_duration_seconds(block)
        narration = _extract_narration(block)
        beats = _infer_beats(narration)
        plot_points.append(
            {
                "id": plot_id,
                "title": title,
                "characters": characters,
                "scenes": scenes,
                "shot_group_type": shot_group_type,
                "duration_seconds": duration_seconds,
                "beats": beats,
                "safe_zone": {"head_seconds": 0.5, "tail_seconds": 0.5},
                "narration": narration,
            }
        )

    payload = {
        "episode": episode,
        "plot_points": plot_points,
        "characters": _extract_table_rows(text, "## 人物清单"),
        "scenes": _extract_table_rows(text, "## 场景清单"),
        "rule_flags": [],
    }
    validate_director_payload(payload)
    return payload


def validate_director_payload(payload: dict[str, Any]) -> None:
    _assert_string(payload.get("episode"), "director.episode")
    plot_points = _assert_list(payload.get("plot_points"), "director.plot_points")
    if not plot_points:
        raise ValueError("director.plot_points 不能为空")
    _assert_list(payload.get("characters"), "director.characters")
    _assert_list(payload.get("scenes"), "director.scenes")
    _assert_list(payload.get("rule_flags"), "director.rule_flags")
    for index, plot_point in enumerate(plot_points):
        label = f"director.plot_points[{index}]"
        _assert_string(plot_point.get("id"), f"{label}.id")
        _assert_string(plot_point.get("title"), f"{label}.title")
        _assert_list(plot_point.get("characters"), f"{label}.characters")
        _assert_list(plot_point.get("scenes"), f"{label}.scenes")
        _assert_string(plot_point.get("shot_group_type"), f"{label}.shot_group_type")
        duration = plot_point.get("duration_seconds")
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"{label}.duration_seconds 必须为正数")
        _assert_list(plot_point.get("beats"), f"{label}.beats")
        safe_zone = plot_point.get("safe_zone")
        if not isinstance(safe_zone, dict):
            raise ValueError(f"{label}.safe_zone 必须为对象")
        for key in ("head_seconds", "tail_seconds"):
            value = safe_zone.get(key)
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{label}.safe_zone.{key} 必须为非负数")
        _assert_string(plot_point.get("narration"), f"{label}.narration")


def build_director_validation(payload: dict[str, Any]) -> dict[str, Any]:
    validate_director_payload(payload)
    issues: list[dict[str, Any]] = []
    for plot_point in payload["plot_points"]:
        narration = plot_point["narration"]
        sentences = _split_sentences(narration)
        plot_id = plot_point["id"]
        duration_seconds = float(plot_point["duration_seconds"])
        key_beats = _estimate_key_beat_count(narration)
        max_beats = max(1, math.floor(max(duration_seconds - 1.0, 0) / 2.5))
        if len(sentences) < 2:
            issues.append(_validation_issue("DIRECTOR_SHORT_NARRATION", plot_id, "导演阐述句数不足，难以支撑动作链与镜头链。"))
        if _contains_any(narration, ABSTRACT_WORDS) and not _contains_any(narration, ACTION_HINTS):
            issues.append(_validation_issue("DIRECTOR_ABSTRACT_ONLY", plot_id, "出现抽象情绪词，但缺少对应物理动作承载。"))
        if not _contains_any(narration, CAMERA_HINTS):
            issues.append(_validation_issue("DIRECTOR_CAMERA_DIRECTION_MISSING", plot_id, "缺少镜头方向或运镜描述。"))
        if not _contains_any(narration, LIGHT_HINTS):
            issues.append(_validation_issue("DIRECTOR_LIGHT_SPECIFICITY_MISSING", plot_id, "缺少具体光源、方向或色温描述。"))
        if sum(1 for beat in plot_point["beats"] if beat["type"] == "action") < 1:
            issues.append(_validation_issue("DIRECTOR_ACTION_CHAIN_MISSING", plot_id, "缺少明确动作链。"))
        if key_beats > max_beats + 1:
            issues.append(
                _validation_issue(
                    "DIRECTOR_BEAT_DENSITY_OVERFLOW",
                    plot_id,
                    f"时长 {duration_seconds}s 估算关键节拍 {key_beats} 个，超过建议上限 {max_beats}。",
                )
            )
        if _contains_any(narration, SAFE_ZONE_HEAD_HINTS) or _contains_any(narration, SAFE_ZONE_TAIL_HINTS):
            issues.append(_validation_issue("DIRECTOR_SAFE_ZONE_RISK", plot_id, "疑似把关键动作压在头尾安全区。"))
    return {
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "summary": {
            "plot_point_count": len(payload["plot_points"]),
            "character_count": len(payload["characters"]),
            "scene_count": len(payload["scenes"]),
        },
        "updated_at": _timestamp(),
    }


def parse_seedance_markdown(episode: str, text: str) -> dict[str, Any]:
    reference_rows = _extract_table_rows(text, "## 素材对应表")
    prompts: list[dict[str, Any]] = []
    matches = list(PLOT_HEADING_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : block_end].strip()
        prompt_text = _extract_bold_labeled_value(block, "Seedance 2.0 提示词")
        refs = REFERENCE_PATTERN.findall(prompt_text)
        prompts.append(
            {
                "id": match.group(1).strip(),
                "title": match.group(2).strip(),
                "prompt_text": prompt_text,
                "reference_usage": refs,
                "image_reference_count": len(refs),
                "audio_design_items": _extract_audio_items(prompt_text),
            }
        )

    payload = {
        "episode": episode,
        "references": reference_rows,
        "prompts": prompts,
        "validation_summary": {
            "prompt_count": len(prompts),
            "reference_count": len(reference_rows),
        },
    }
    validate_seedance_payload(payload)
    return payload


def validate_seedance_payload(payload: dict[str, Any]) -> None:
    _assert_string(payload.get("episode"), "seedance.episode")
    _assert_list(payload.get("references"), "seedance.references")
    prompts = _assert_list(payload.get("prompts"), "seedance.prompts")
    if not prompts:
        raise ValueError("seedance.prompts 不能为空")
    summary = payload.get("validation_summary")
    if not isinstance(summary, dict):
        raise ValueError("seedance.validation_summary 必须为对象")
    for index, prompt in enumerate(prompts):
        label = f"seedance.prompts[{index}]"
        _assert_string(prompt.get("id"), f"{label}.id")
        _assert_string(prompt.get("title"), f"{label}.title")
        _assert_string(prompt.get("prompt_text"), f"{label}.prompt_text")
        _assert_list(prompt.get("reference_usage"), f"{label}.reference_usage")
        count = prompt.get("image_reference_count")
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"{label}.image_reference_count 必须为非负整数")
        _assert_list(prompt.get("audio_design_items"), f"{label}.audio_design_items")


def build_seedance_validation(payload: dict[str, Any], reference_map: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_seedance_payload(payload)
    issues: list[dict[str, Any]] = []
    valid_refs = {item["ref_id"] for item in reference_map.get("references", [])} if reference_map else set()
    for prompt in payload["prompts"]:
        prompt_id = prompt["id"]
        prompt_text = prompt["prompt_text"]
        if prompt["image_reference_count"] > 9:
            issues.append(_validation_issue("SEEDANCE_IMAGE_REFERENCE_OVER_LIMIT", prompt_id, "图片引用数量超过 9 张上限。"))
        if len(set(prompt["reference_usage"])) > 12:
            issues.append(_validation_issue("SEEDANCE_TOTAL_REFERENCE_OVER_LIMIT", prompt_id, "总素材引用数量超过 12 个。"))
        if not prompt["audio_design_items"]:
            issues.append(_validation_issue("SEEDANCE_AUDIO_DESIGN_MISSING", prompt_id, "缺少可执行的音频或环境音设计。"))
        if "宫格" in prompt_text or "九宫格" in prompt_text:
            issues.append(_validation_issue("SEEDANCE_SCENE_GRID_USED_DIRECTLY", prompt_id, "疑似直接引用整张宫格图，而不是独立场景拆图。"))
        if reference_map:
            for ref_id in prompt["reference_usage"]:
                if ref_id not in valid_refs:
                    issues.append(_validation_issue("SEEDANCE_REFERENCE_NOT_REGISTERED", prompt_id, f"引用 {ref_id} 未在 reference-map 中登记。"))
        duration_seconds = _extract_declared_duration_seconds(prompt_text)
        if duration_seconds is not None:
            key_beats = _estimate_key_beat_count(prompt_text)
            max_beats = max(1, math.floor(max(duration_seconds - 1.0, 0) / 2.5))
            if key_beats > max_beats + 1:
                issues.append(
                    _validation_issue(
                        "SEEDANCE_BEAT_DENSITY_OVERFLOW",
                        prompt_id,
                        f"时长 {duration_seconds}s 估算关键节拍 {key_beats} 个，超过建议上限 {max_beats}。",
                    )
                )
        if _contains_any(prompt_text, SAFE_ZONE_HEAD_HINTS) or _contains_any(prompt_text, SAFE_ZONE_TAIL_HINTS):
            issues.append(_validation_issue("SEEDANCE_SAFE_ZONE_RISK", prompt_id, "疑似把关键动作或台词压在头尾安全区。"))
    return {
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "summary": {
            "prompt_count": len(payload["prompts"]),
            "reference_count": len(payload["references"]),
        },
        "updated_at": _timestamp(),
    }


def build_design_validation(character_content: str, scene_content: str) -> dict[str, Any]:
    panel_count = len(re.findall(r"格\d+\s*[—-]", scene_content))
    declared_grid_spec = _extract_declared_grid_spec(scene_content)
    checks = {
        "character_has_output_requirements": "**出图要求**" in character_content,
        "character_has_prompt": "**提示词**" in character_content,
        "scene_has_visual_spec": "### 视觉规范" in scene_content,
        "scene_has_panel_breakdown": "### Panel Breakdown" in scene_content,
        "scene_has_declared_grid_spec": bool(declared_grid_spec),
        "scene_has_panels": panel_count > 0,
    }
    issues = [
        _validation_issue("DESIGN_STRUCTURE_MISSING", "design", f"缺少结构项：{name}")
        for name, passed in checks.items()
        if not passed
    ]
    if panel_count > 0 and panel_count <= 16:
        expected_grid_spec = choose_grid_spec(panel_count)
        if declared_grid_spec and declared_grid_spec != expected_grid_spec:
            issues.append(
                _validation_issue(
                    "DESIGN_GRID_SPEC_MISMATCH",
                    "design",
                    f"当前拆图数量为 {panel_count}，应使用 {expected_grid_spec}，但文稿声明为 {declared_grid_spec}。",
                )
            )
    elif panel_count > 16:
        issues.append(_validation_issue("DESIGN_PANEL_COUNT_OVER_LIMIT", "design", "场景拆图数量超过 16，超出当前宫格规格支持范围。"))
    return {
        "result": "PASS" if not issues else "FAIL",
        "issues": issues,
        "checks": {
            **checks,
            "panel_count": panel_count,
            "declared_grid_spec": declared_grid_spec,
        },
        "updated_at": _timestamp(),
    }


def parse_business_review_payload(payload: dict[str, Any]) -> ReviewOutcome:
    result = _require_enum(payload.get("result"), {"PASS", "FAIL"}, "business.result")
    report = _require_non_empty_string(payload.get("report"), "business.report")
    dimension_scores = _normalize_dimension_scores(payload.get("dimension_scores", {}))
    average_score = payload.get("average_score")
    if average_score is not None and not isinstance(average_score, (int, float)):
        raise ValueError("business.average_score 必须为数字")
    has_item_below_6 = payload.get("has_item_below_6")
    if has_item_below_6 is None:
        has_item_below_6 = any(score < 6 for score in dimension_scores.values())
    if not isinstance(has_item_below_6, bool):
        raise ValueError("business.has_item_below_6 必须为布尔值")
    return ReviewOutcome(
        result=result,
        report=report,
        issues=_normalize_issue_messages(payload.get("issues", [])),
        average_score=float(average_score) if average_score is not None else None,
        has_item_below_6=has_item_below_6,
        dimension_scores=dimension_scores,
        raw_payload=payload,
    )


def parse_compliance_review_payload(payload: dict[str, Any]) -> ReviewOutcome:
    result = _require_enum(payload.get("result"), {"PASS", "FAIL"}, "compliance.result")
    report = _require_non_empty_string(payload.get("report"), "compliance.report")
    violations = payload.get("violations", [])
    if not isinstance(violations, list):
        raise ValueError("compliance.violations 必须为数组")
    raw_issues = payload.get("issues", [])
    if not isinstance(raw_issues, list):
        raise ValueError("compliance.issues 必须为数组")
    return ReviewOutcome(
        result=result,
        report=report,
        issues=_normalize_issue_messages(raw_issues) or _normalize_issue_messages(violations),
        violations=[item for item in violations if isinstance(item, dict)],
        raw_payload=payload,
    )


def can_auto_accept_review(business: ReviewOutcome, compliance: ReviewOutcome) -> bool:
    return (
        business.result == "PASS"
        and compliance.result == "PASS"
        and business.average_score is not None
        and business.average_score >= 8
        and business.has_item_below_6 is False
    )


def _extract_labeled_value(block: str, label: str) -> str:
    match = re.search(rf"-\s*{re.escape(label)}[：:]\s*(.+)", block)
    return match.group(1).strip() if match else ""


def _extract_bold_labeled_value(block: str, label: str) -> str:
    match = re.search(rf"\*\*{re.escape(label)}\*\*[：:]\s*(.+)", block, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_duration_seconds(block: str) -> float:
    match = re.search(r"-\s*时长建议[：:]\s*(\d+(?:\.\d+)?)s", block, re.IGNORECASE)
    return float(match.group(1)) if match else 1.0


def _extract_narration(block: str) -> str:
    narration = _extract_bold_labeled_value(block, "导演阐述")
    if not narration:
        raise ValueError("导演产物缺少 **导演阐述** 段落")
    return narration


def _extract_table_rows(text: str, heading: str) -> list[dict[str, str]]:
    section = _extract_section(text, heading)
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 2:
        return []
    headers = [item.strip() for item in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        match = TABLE_ROW_PATTERN.match(line)
        if not match:
            continue
        values = [item.strip() for item in line.strip("|").split("|")]
        if len(values) != len(headers):
            continue
        rows.append(dict(zip(headers, values, strict=False)))
    return rows


def _extract_section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    remaining = text[start + len(heading) :]
    next_heading = re.search(r"\n##\s+", remaining)
    if not next_heading:
        return remaining.strip()
    return remaining[: next_heading.start()].strip()


def _split_inline_values(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[、,，/]", value) if item.strip()]


def _infer_beats(narration: str) -> list[dict[str, str]]:
    beats: list[dict[str, str]] = []
    for sentence in _split_sentences(narration):
        beat_type = "action"
        if _contains_any(sentence, CAMERA_HINTS):
            beat_type = "camera"
        elif _contains_any(sentence, LIGHT_HINTS):
            beat_type = "lighting"
        beats.append({"type": beat_type, "text": sentence})
    return beats


def _extract_audio_items(prompt_text: str) -> list[str]:
    items: list[str] = []
    for sentence in _split_sentences(prompt_text):
        if _contains_any(sentence, AUDIO_HINTS):
            items.append(sentence)
    return items


def _extract_declared_grid_spec(text: str) -> str | None:
    match = re.search(r"(3\s*[x×]\s*3|3\s*[x×]\s*4|4\s*[x×]\s*4)", text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower().replace("×", "x").replace(" ", "")


def _extract_declared_duration_seconds(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:秒|s)", text, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1))


def _estimate_key_beat_count(text: str) -> int:
    count = 0
    for sentence in _split_sentences(text):
        segments = [item.strip() for item in re.split(r"[，,、]", sentence) if item.strip()]
        segment_hits = 0
        for segment in segments:
            if _contains_any(segment, ACTION_HINTS) or _contains_any(segment, CAMERA_HINTS):
                segment_hits += 1
        count += segment_hits
    return count


def _split_sentences(text: str) -> list[str]:
    return [item.strip() for item in SENTENCE_SPLIT_PATTERN.split(text) if item.strip()]


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    return any(hint in text for hint in hints)


def _validation_issue(code: str, location: str, message: str) -> dict[str, Any]:
    return {"code": code, "location": location, "message": message}


def _normalize_issue_messages(items: Any) -> list[str]:
    if not isinstance(items, list):
        raise ValueError("issues 必须为数组")
    normalized: list[str] = []
    for item in items:
        if isinstance(item, str):
            if item.strip():
                normalized.append(item.strip())
            continue
        if isinstance(item, dict):
            problem = item.get("problem") or item.get("message") or item.get("detail") or "未命名问题"
            location = item.get("location")
            severity = item.get("severity")
            fragments = [str(problem).strip()]
            if location:
                fragments.append(f"位置:{location}")
            if severity:
                fragments.append(f"级别:{severity}")
            normalized.append("；".join(fragments))
            continue
        raise ValueError("issues 数组仅支持字符串或对象")
    return normalized


def _normalize_dimension_scores(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError("business.dimension_scores 必须为对象")
    normalized: dict[str, float] = {}
    for key, score in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("business.dimension_scores 键必须为非空字符串")
        if not isinstance(score, (int, float)):
            raise ValueError(f"business.dimension_scores.{key} 必须为数字")
        normalized[key.strip()] = float(score)
    return normalized


def _assert_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 必须为非空字符串")
    return value.strip()


def _assert_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} 必须为数组")
    return value


def _require_non_empty_string(value: Any, label: str) -> str:
    return _assert_string(value, label)


def _require_enum(value: Any, allowed: set[str], label: str) -> str:
    normalized = _assert_string(value, label).upper()
    if normalized not in allowed:
        raise ValueError(f"{label} 必须属于 {sorted(allowed)}")
    return normalized


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
