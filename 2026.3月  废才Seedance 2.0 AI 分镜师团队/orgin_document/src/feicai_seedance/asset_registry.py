from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .logging_utils import append_jsonl
from .utils import safe_relative_path

CHARACTER_HEADING_PATTERN = re.compile(r"^##\s+(.+?)(?:（(.+?)）)?\s*$", re.MULTILINE)
SCENE_HEADING_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
PANEL_PATTERN = re.compile(r"格(\d+)\s*[—-]+\s*【(.+?)】")


def sync_design_assets(project_root: Path, episode: str, character_content: str, scene_content: str) -> dict[str, Any]:
    registry = _load_registry(project_root)
    character_assets = _parse_character_assets(episode, character_content, registry)
    scene_assets = _parse_scene_assets(episode, scene_content, registry)
    all_assets = registry["assets"]
    indexed = {item["asset_id"]: item for item in all_assets}
    for asset in [*character_assets, *scene_assets]:
        indexed[asset["asset_id"]] = asset
    registry["assets"] = sorted(indexed.values(), key=lambda item: item["asset_id"])
    registry["updated_at"] = _timestamp()
    _save_registry(project_root, registry)
    return {
        "episode": episode,
        "character_assets": character_assets,
        "scene_assets": scene_assets,
        "updated_at": registry["updated_at"],
    }


def register_asset_image(
    project_root: Path,
    asset_id: str,
    image_path: str,
    source_tool: str = "manual",
) -> dict[str, Any]:
    registry = _load_registry(project_root)
    asset = next((item for item in registry["assets"] if item["asset_id"] == asset_id), None)
    if asset is None:
        raise RuntimeError(f"Asset not found: {asset_id}")

    source = _resolve_source_path(project_root, image_path)
    if not source.exists() or not source.is_file():
        raise RuntimeError(f"Image file not found: {source}")

    destination = _image_destination(project_root, asset, source.suffix or ".png")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)

    relative_destination = destination.resolve().relative_to(project_root.resolve())
    asset["image_path"] = str(relative_destination).replace("\\", "/")
    asset["status"] = "READY_FOR_STORYBOARD" if asset["asset_type"] != "scene_grid" else "IMAGE_REGISTERED"
    asset["source_tool"] = source_tool
    asset["updated_at"] = _timestamp()
    registry["updated_at"] = asset["updated_at"]
    _save_registry(project_root, registry)
    append_jsonl(
        project_root / "assets" / "manifests" / "image-generation-log.jsonl",
        {
            "asset_id": asset_id,
            "asset_type": asset["asset_type"],
            "episode": asset["episode_origin"],
            "image_path": asset["image_path"],
            "source_tool": source_tool,
            "status": asset["status"],
        },
    )
    return asset


def build_reference_map(project_root: Path, episode: str) -> dict[str, Any]:
    registry = _load_registry(project_root)
    director_path = project_root / "outputs" / episode / "01-director-analysis.json"
    if not director_path.exists():
        raise RuntimeError(f"Missing director JSON: {director_path}")
    director = json.loads(director_path.read_text(encoding="utf-8"))
    ready_assets = [item for item in registry["assets"] if item["status"] == "READY_FOR_STORYBOARD"]
    references: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for plot_point in director.get("plot_points", []):
        for character_name in plot_point.get("characters", []):
            asset = _pick_ready_asset(ready_assets, asset_type="character", name=character_name)
            if asset is None:
                missing.append({"plot_point": plot_point["id"], "asset_type": "character", "name": character_name})
                continue
            references.append(_build_reference_entry(references, asset, f"{plot_point['id']} 人物 {character_name}"))
        for scene_name in plot_point.get("scenes", []):
            asset = _pick_scene_asset(ready_assets, scene_name)
            if asset is None:
                missing.append({"plot_point": plot_point["id"], "asset_type": "scene", "name": scene_name})
                continue
            references.append(_build_reference_entry(references, asset, f"{plot_point['id']} 场景 {scene_name}"))

    deduped: list[dict[str, Any]] = []
    seen_asset_ids: dict[str, str] = {}
    for item in references:
        existing_ref = seen_asset_ids.get(item["asset_id"])
        if existing_ref:
            continue
        seen_asset_ids[item["asset_id"]] = item["ref_id"]
        deduped.append(item)

    payload = {
        "episode": episode,
        "references": deduped,
        "missing_assets": missing,
        "updated_at": _timestamp(),
    }
    output_path = project_root / "outputs" / episode / "reference-map.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def ready_asset_summary(project_root: Path, episode: str) -> str:
    reference_map_path = project_root / "outputs" / episode / "reference-map.json"
    if not reference_map_path.exists():
        return "（reference-map 尚未生成）"
    payload = json.loads(reference_map_path.read_text(encoding="utf-8"))
    lines = []
    for item in payload.get("references", []):
        lines.append(
            f"- {item['ref_id']} | {item['asset_type']} | {item['name']} | {item['file_path']}"
        )
    if not lines:
        return "（无已就绪引用资产）"
    return "\n".join(lines)


def load_reference_map(project_root: Path, episode: str) -> dict[str, Any]:
    path = project_root / "outputs" / episode / "reference-map.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_asset_registry(project_root: Path) -> dict[str, Any]:
    return _load_registry(project_root)


def _parse_character_assets(episode: str, content: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    matches = list(CHARACTER_HEADING_PATTERN.finditer(content))
    assets: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        block = content[match.start() : block_end].strip()
        name = match.group(1).strip()
        meta = (match.group(2) or "").strip()
        existing = _find_existing_asset(registry, "character", episode, name)
        asset_id = existing["asset_id"] if existing else _make_asset_id("char", episode, name)
        status = existing["status"] if existing and existing.get("image_path") else "PROMPT_DRAFTED"
        assets.append(
            {
                "asset_id": asset_id,
                "asset_type": "character",
                "name": name,
                "episode_origin": episode,
                "status": status,
                "prompt_entry_ref": f"assets/character-prompts.md#{name}",
                "prompt_text_path": "assets/character-prompts.md",
                "image_path": existing.get("image_path") if existing else None,
                "variant_of": _infer_variant_of(meta, registry),
                "tags": [item for item in [meta] if item],
                "source_version": 1,
                "source_tool": existing.get("source_tool", "prompt") if existing else "prompt",
                "updated_at": _timestamp(),
                "prompt_excerpt": _extract_prompt_excerpt(block),
            }
        )
    return assets


def _parse_scene_assets(episode: str, content: str, registry: dict[str, Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    scene_match = SCENE_HEADING_PATTERN.search(content)
    grid_name = scene_match.group(1).strip() if scene_match else f"{episode} 场景宫格"
    existing_grid = _find_existing_asset(registry, "scene_grid", episode, grid_name)
    grid_asset_id = existing_grid["asset_id"] if existing_grid else _make_asset_id("scenegrid", episode, grid_name)
    assets.append(
        {
            "asset_id": grid_asset_id,
            "asset_type": "scene_grid",
            "name": grid_name,
            "episode_origin": episode,
            "status": existing_grid["status"] if existing_grid and existing_grid.get("image_path") else "PROMPT_DRAFTED",
            "prompt_entry_ref": f"assets/scene-prompts.md#{grid_name}",
            "prompt_text_path": "assets/scene-prompts.md",
            "image_path": existing_grid.get("image_path") if existing_grid else None,
            "variant_of": None,
            "tags": [grid_name],
            "source_version": 1,
            "source_tool": existing_grid.get("source_tool", "prompt") if existing_grid else "prompt",
            "updated_at": _timestamp(),
            "prompt_excerpt": _extract_prompt_excerpt(content),
        }
    )
    for panel_number, panel_name in PANEL_PATTERN.findall(content):
        existing = _find_existing_asset(registry, "scene_panel", episode, panel_name)
        asset_id = existing["asset_id"] if existing else _make_asset_id("scene", episode, f"{panel_name}-{panel_number}")
        assets.append(
            {
                "asset_id": asset_id,
                "asset_type": "scene_panel",
                "name": panel_name,
                "episode_origin": episode,
                "status": existing["status"] if existing and existing.get("image_path") else "IMAGE_PENDING",
                "prompt_entry_ref": f"assets/scene-prompts.md#{grid_name}",
                "prompt_text_path": "assets/scene-prompts.md",
                "image_path": existing.get("image_path") if existing else None,
                "variant_of": grid_asset_id,
                "tags": [f"panel-{panel_number}", grid_name],
                "source_version": 1,
                "source_tool": existing.get("source_tool", "prompt") if existing else "prompt",
                "updated_at": _timestamp(),
                "prompt_excerpt": panel_name,
            }
        )
    return assets


def _load_registry(project_root: Path) -> dict[str, Any]:
    registry_path = project_root / "assets" / "registry" / "asset-registry.json"
    if not registry_path.exists():
        raise RuntimeError(f"Missing asset registry: {registry_path}")
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if "assets" not in payload or not isinstance(payload["assets"], list):
        raise RuntimeError("asset-registry.json 格式不正确")
    return payload


def _save_registry(project_root: Path, registry: dict[str, Any]) -> None:
    registry_root = project_root / "assets" / "registry"
    registry_root.mkdir(parents=True, exist_ok=True)
    (registry_root / "asset-registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    character_index = {
        "version": "1.0",
        "updated_at": registry["updated_at"],
        "characters": [
            {"asset_id": item["asset_id"], "name": item["name"], "status": item["status"], "image_path": item.get("image_path")}
            for item in registry["assets"]
            if item["asset_type"] == "character"
        ],
    }
    scene_index = {
        "version": "1.0",
        "updated_at": registry["updated_at"],
        "scenes": [
            {
                "asset_id": item["asset_id"],
                "name": item["name"],
                "status": item["status"],
                "asset_type": item["asset_type"],
                "image_path": item.get("image_path"),
            }
            for item in registry["assets"]
            if item["asset_type"] in {"scene_grid", "scene_panel"}
        ],
    }
    (registry_root / "character-index.json").write_text(json.dumps(character_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (registry_root / "scene-index.json").write_text(json.dumps(scene_index, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_existing_asset(registry: dict[str, Any], asset_type: str, episode: str, name: str) -> dict[str, Any] | None:
    for item in registry["assets"]:
        if item["asset_type"] == asset_type and item["episode_origin"] == episode and item["name"] == name:
            return item
    return None


def _infer_variant_of(meta: str, registry: dict[str, Any]) -> str | None:
    if "变体" not in meta:
        return None
    for item in registry["assets"]:
        if item["asset_type"] == "character":
            return item["asset_id"]
    return None


def _extract_prompt_excerpt(text: str, limit: int = 160) -> str:
    excerpt = re.sub(r"\s+", " ", text).strip()
    return excerpt[:limit]


def _make_asset_id(prefix: str, episode: str, name: str) -> str:
    digest = hashlib.sha1(f"{episode}:{name}".encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{episode}-{digest}-v1"


def _resolve_source_path(project_root: Path, image_path: str) -> Path:
    candidate = Path(image_path)
    if candidate.is_absolute():
        return candidate.resolve()
    return safe_relative_path(project_root.resolve(), image_path)


def _image_destination(project_root: Path, asset: dict[str, Any], suffix: str) -> Path:
    assets_root = project_root / "assets" / "library"
    if asset["asset_type"] == "character":
        base = assets_root / "characters"
    elif asset["asset_type"] == "scene_panel":
        base = assets_root / "scene-panels"
    else:
        base = assets_root / "scenes"
    return base / f"{asset['asset_id']}{suffix}"


def _pick_ready_asset(assets: list[dict[str, Any]], asset_type: str, name: str) -> dict[str, Any] | None:
    normalized = name.strip().lower()
    for item in assets:
        if item["asset_type"] != asset_type:
            continue
        if item["name"].strip().lower() == normalized:
            return item
    for item in assets:
        if item["asset_type"] != asset_type:
            continue
        if normalized in item["name"].strip().lower() or item["name"].strip().lower() in normalized:
            return item
    return None


def _pick_scene_asset(assets: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for asset_type in ("scene_panel", "scene"):
        asset = _pick_ready_asset(assets, asset_type, name)
        if asset:
            return asset
    return None


def _build_reference_entry(existing: list[dict[str, Any]], asset: dict[str, Any], purpose: str) -> dict[str, Any]:
    ref_id = f"@图片{len(existing) + 1}"
    return {
        "ref_id": ref_id,
        "asset_id": asset["asset_id"],
        "asset_type": asset["asset_type"],
        "name": asset["name"],
        "file_path": asset["image_path"],
        "purpose": purpose,
    }


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
