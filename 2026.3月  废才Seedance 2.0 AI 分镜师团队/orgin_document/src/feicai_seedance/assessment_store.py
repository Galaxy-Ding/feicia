from __future__ import annotations

from pathlib import Path
from typing import Any

from .acceptance_store import load_acceptance_state
from .review_store import load_review_summary

POSITIVE_HINTS = (
    "基本通过",
    "基本准确",
    "基本成立",
    "完成度高",
    "质量较高",
    "整体完成度高",
    "收束有力",
    "合格",
    "可用水平",
    "覆盖完整",
    "风格统一",
)

STAGE_SEQUENCE = ("director", "design", "prompt")


def quality_band(score: float | None) -> str:
    if score is None:
        return "未提取到评分"
    if score >= 9.0:
        return "优秀，可优先放行"
    if score >= 8.0:
        return "良好，但仍需人工判断缺口"
    if score >= 7.5:
        return "可用，但存在明显缺口"
    return "未达到建议放行线"


def recommendation_label(recommendation: str) -> str:
    mapping = {
        "auto_accept": "可自动放行",
        "manual_accept_candidate": "建议人工复核后放行",
        "manual_reject_candidate": "建议先修改后再审",
        "manual_review_required": "缺少结构化评分，必须人工判断",
    }
    return mapping.get(recommendation, "需要人工判断")


def extract_highlights(report: str, limit: int = 3) -> list[str]:
    highlights: list[str] = []
    for raw_line in report.splitlines():
        line = _clean_line(raw_line)
        if not line or len(line) < 8:
            continue
        if _looks_like_table_row(raw_line):
            continue
        if any(hint in line for hint in POSITIVE_HINTS) and line not in highlights:
            highlights.append(line)
        if len(highlights) >= limit:
            break
    return highlights


def save_stage_assessment_report(reports_root: Path, episode: str, stage: str) -> Path:
    summary = load_review_summary(reports_root, episode, stage)
    if not summary:
        raise RuntimeError(f"Missing review summary for {episode} {stage}")

    acceptance_state = load_acceptance_state(reports_root, episode)
    stage_state = acceptance_state.get("stages", {}).get(stage, {})
    business = summary.get("business", {})
    compliance = summary.get("compliance", {})
    business_report_path = Path(business["report_path"])
    compliance_report_path = Path(compliance["report_path"])
    business_report = business_report_path.read_text(encoding="utf-8") if business_report_path.exists() else ""
    compliance_report = compliance_report_path.read_text(encoding="utf-8") if compliance_report_path.exists() else ""
    business_issues = business.get("issues", [])
    compliance_issues = compliance.get("issues", [])
    report_path = reports_root / "assessments" / episode / f"{stage}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    recommendation = summary.get("recommendation", "manual_review_required")
    score = business.get("average_score")
    highlights = extract_highlights(business_report)
    if not highlights:
        highlights = ["未从审核正文中提取到显式亮点，请直接阅读完整业务审核报告。"]

    fail_items = compliance_issues if compliance_issues else business_issues
    if not fail_items:
        fail_items = ["当前轮次未记录否决项。"]

    content = (
        f"# {episode} {stage} 人工审核决策报告\n\n"
        "## 1. 当前结论\n\n"
        f"- 当前状态: {stage_state.get('status', 'not_started')}\n"
        f"- 当前来源: {stage_state.get('source', 'system')}\n"
        f"- 业务结果: {business.get('result', 'UNKNOWN')}\n"
        f"- 业务评分: {score if score is not None else 'n/a'}/10\n"
        f"- 单项低于 6: {business.get('has_item_below_6', 'n/a')}\n"
        f"- 质量分层: {quality_band(score)}\n"
        f"- 合规结果: {compliance.get('result', 'UNKNOWN')}\n"
        f"- 系统建议: {recommendation_label(recommendation)} ({recommendation})\n\n"
        "## 2. 哪些地方做得好\n\n"
        + _render_bullets(highlights)
        + "\n\n## 3. 哪些地方还不够出色\n\n"
        + _render_bullets(business_issues or ["当前轮次未记录一般问题。"])
        + "\n\n## 4. 当前不合格项 / 否决项\n\n"
        + _render_bullets(fail_items)
        + "\n\n## 5. 人工决策建议\n\n"
        f"- 建议动作: {recommendation_label(recommendation)}\n"
        f"- 如果决定放行: `python -m feicai_seedance.cli accept {episode} {stage}`\n"
        f"- 如果决定返修: `python -m feicai_seedance.cli revise {episode} {stage_to_revise_scope(stage)} \"<feedback>\"`\n"
        f"- 如果只看报告: `python -m feicai_seedance.cli review {episode} {stage}`\n\n"
        "## 6. 证据文件\n\n"
        f"- review_summary: {reports_root / 'reviews' / episode / stage / 'summary.json'}\n"
        f"- business_report: {business_report_path}\n"
        f"- compliance_report: {compliance_report_path}\n"
        f"- acceptance_state: {reports_root / 'acceptance' / f'{episode}.json'}\n\n"
        "## 7. 审核正文摘录\n\n"
        "### Business Review\n\n"
        + (business_report or "missing business review report")
        + "\n\n### Compliance Review\n\n"
        + (compliance_report or "missing compliance review report")
        + "\n"
    )
    report_path.write_text(content, encoding="utf-8")
    return report_path


def save_episode_assessment_overview(reports_root: Path, episode: str, stages: list[str] | None = None) -> Path:
    selected = stages or list(STAGE_SEQUENCE)
    acceptance_state = load_acceptance_state(reports_root, episode)
    lines = [
        f"# {episode} 人工审核总览",
        "",
        "| Stage | Status | Business | Score | Compliance | Recommendation | Report |",
        "|---|---|---|---|---|---|---|",
    ]
    for stage in selected:
        summary = load_review_summary(reports_root, episode, stage)
        state = acceptance_state.get("stages", {}).get(stage, {})
        report_path = reports_root / "assessments" / episode / f"{stage}.md"
        lines.append(
            "| "
            + " | ".join(
                [
                    stage,
                    state.get("status", "not_started"),
                    str(summary.get("business", {}).get("result", "UNKNOWN")),
                    str(summary.get("business", {}).get("average_score", "n/a")),
                    str(summary.get("compliance", {}).get("result", "UNKNOWN")),
                    str(summary.get("recommendation", "n/a")),
                    str(report_path),
                ]
            )
            + " |"
        )
    path = reports_root / "assessments" / episode / "overview.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_stage_assessment_snapshot(reports_root: Path, episode: str, stage: str) -> dict[str, Any]:
    summary = load_review_summary(reports_root, episode, stage)
    if not summary:
        raise RuntimeError(f"Missing review summary for {episode} {stage}")
    business = summary.get("business", {})
    compliance = summary.get("compliance", {})
    score = business.get("average_score")
    return {
        "episode": episode,
        "stage": stage,
        "business_result": business.get("result", "UNKNOWN"),
        "business_score": score,
        "quality_band": quality_band(score),
        "compliance_result": compliance.get("result", "UNKNOWN"),
        "recommendation": summary.get("recommendation", "manual_review_required"),
    }


def stage_to_revise_scope(stage: str) -> str:
    mapping = {"director": "director", "design": "art", "prompt": "storyboard"}
    return mapping[stage]


def _clean_line(value: str) -> str:
    return value.strip().lstrip("-").strip()


def _looks_like_table_row(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("|") or stripped.startswith("**") or stripped.startswith("---")


def _render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)
