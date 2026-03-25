from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .acceptance_store import STAGES, get_stage_status
from .asset_registry import load_asset_registry, load_reference_map
from .config import load_config

SAMPLE_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def generate_acceptance_evidence(project_root: Path, episode: str) -> dict[str, Any]:
    root = project_root.resolve()
    config = load_config(root)
    reports_root = config.paths.reports
    outputs_root = config.paths.outputs / episode
    review_root = reports_root / "reviews" / episode
    assessment_root = reports_root / "assessments" / episode
    acceptance_root = reports_root / "acceptance" / episode

    required_files = [
        ("director_markdown", outputs_root / "01-director-analysis.md"),
        ("director_json", outputs_root / "01-director-analysis.json"),
        ("design_validation", outputs_root / "validation" / "design-validation.json"),
        ("prompt_markdown", outputs_root / "02-seedance-prompts.md"),
        ("prompt_json", outputs_root / "02-seedance-prompts.json"),
        ("prompt_validation", outputs_root / "validation" / "prompt-validation.json"),
        ("director_validation", outputs_root / "validation" / "director-validation.json"),
        ("reference_map", outputs_root / "reference-map.json"),
        ("assessment_overview", assessment_root / "overview.md"),
        ("review_director_summary", review_root / "director" / "summary.json"),
        ("review_design_summary", review_root / "design" / "summary.json"),
        ("review_prompt_summary", review_root / "prompt" / "summary.json"),
        ("asset_registry", config.paths.assets / "registry" / "asset-registry.json"),
        ("image_manifest", config.paths.assets / "manifests" / "image-generation-log.jsonl"),
    ]

    stage_statuses = {stage: get_stage_status(reports_root, episode, stage) for stage in STAGES}
    registry = load_asset_registry(root)
    episode_assets = [item for item in registry.get("assets", []) if item.get("episode_origin") == episode]
    ready_assets = [item for item in episode_assets if item.get("status") == "READY_FOR_STORYBOARD"]
    variant_assets = [item for item in episode_assets if item.get("variant_of")]
    reference_map = load_reference_map(root, episode)

    golden_dir = config.paths.assets / "acceptance" / episode / "golden"
    variant_dir = config.paths.assets / "acceptance" / episode / "variants"
    golden_samples = _collect_sample_files(golden_dir)
    variant_samples = _collect_sample_files(variant_dir)

    checklist = [
        _check_item(label, path.exists(), str(path))
        for label, path in required_files
    ]
    checklist.extend(
        [
            _check_item(
                "all_stages_accepted",
                all(status == "accepted" for status in stage_statuses.values()),
                ", ".join(f"{stage}={status}" for stage, status in stage_statuses.items()),
            ),
            _check_item(
                "reference_map_ready",
                bool(reference_map.get("references")) and not reference_map.get("missing_assets"),
                f"references={len(reference_map.get('references', []))}, missing_assets={len(reference_map.get('missing_assets', []))}",
            ),
            _check_item(
                "golden_samples_present",
                bool(golden_samples),
                str(golden_dir),
            ),
            _check_item(
                "variant_samples_present",
                bool(variant_samples),
                str(variant_dir),
            ),
        ]
    )

    payload = {
        "episode": episode,
        "result": "PASS" if all(item["passed"] for item in checklist) else "FAIL",
        "stage_statuses": stage_statuses,
        "checklist": checklist,
        "asset_summary": {
            "episode_asset_count": len(episode_assets),
            "ready_asset_count": len(ready_assets),
            "variant_asset_count": len(variant_assets),
            "reference_count": len(reference_map.get("references", [])),
            "missing_reference_assets": reference_map.get("missing_assets", []),
        },
        "sample_summary": {
            "golden_dir": str(golden_dir),
            "golden_count": len(golden_samples),
            "golden_files": golden_samples,
            "variant_dir": str(variant_dir),
            "variant_count": len(variant_samples),
            "variant_files": variant_samples,
        },
        "missing_items": [item["name"] for item in checklist if not item["passed"]],
    }

    acceptance_root.mkdir(parents=True, exist_ok=True)
    json_path = acceptance_root / "evidence.json"
    markdown_path = acceptance_root / "evidence.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload, json_path), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["markdown_path"] = str(markdown_path)
    return payload


def _check_item(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def _collect_sample_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SAMPLE_IMAGE_SUFFIXES:
            continue
        files.append(str(path))
    return files


def _render_markdown(payload: dict[str, Any], json_path: Path) -> str:
    lines = [
        f"# {payload['episode']} Acceptance Evidence",
        "",
        f"- Result: {payload['result']}",
        f"- JSON: {json_path}",
        "",
        "## Stage Status",
        "",
    ]
    for stage, status in payload["stage_statuses"].items():
        lines.append(f"- {stage}: {status}")

    lines.extend(["", "## Checklist", ""])
    for item in payload["checklist"]:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- [{marker}] {item['name']}: {item['detail']}")

    asset_summary = payload["asset_summary"]
    lines.extend(
        [
            "",
            "## Asset Summary",
            "",
            f"- episode_asset_count: {asset_summary['episode_asset_count']}",
            f"- ready_asset_count: {asset_summary['ready_asset_count']}",
            f"- variant_asset_count: {asset_summary['variant_asset_count']}",
            f"- reference_count: {asset_summary['reference_count']}",
            f"- missing_reference_assets: {len(asset_summary['missing_reference_assets'])}",
            "",
            "## Sample Summary",
            "",
            f"- golden_count: {payload['sample_summary']['golden_count']}",
            f"- variant_count: {payload['sample_summary']['variant_count']}",
        ]
    )

    if payload["missing_items"]:
        lines.extend(["", "## Missing Items", ""])
        for item in payload["missing_items"]:
            lines.append(f"- {item}")

    return "\n".join(lines) + "\n"
