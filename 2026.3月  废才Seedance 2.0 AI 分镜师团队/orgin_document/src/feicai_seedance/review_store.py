from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ReviewOutcome


def save_review_round(
    reports_root: Path,
    episode: str,
    stage: str,
    round_index: int,
    review_type: str,
    outcome: ReviewOutcome,
) -> Path:
    path = reports_root / "reviews" / episode / stage / f"round-{round_index:02d}-{review_type}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    score_line = f"\n- average_score: {outcome.average_score}\n" if outcome.average_score is not None else "\n"
    below_line = (
        f"- has_item_below_6: {outcome.has_item_below_6}\n" if outcome.has_item_below_6 is not None else ""
    )
    dimension_line = (
        f"- dimension_scores: {json.dumps(outcome.dimension_scores, ensure_ascii=False)}\n"
        if outcome.dimension_scores
        else ""
    )
    violation_line = (
        f"- violations_count: {len(outcome.violations)}\n" if outcome.violations else ""
    )
    content = (
        f"# {episode} {stage} {review_type} review\n\n"
        f"- result: {outcome.result}\n"
        f"- issues_count: {len(outcome.issues)}"
        f"{score_line}"
        f"{below_line}"
        f"{dimension_line}"
        f"{violation_line}"
        f"- generated_at: {datetime.now().astimezone().isoformat(timespec='seconds')}\n\n"
        "## Issues\n\n"
        + ("\n".join(f"- {item}" for item in outcome.issues) if outcome.issues else "- none")
        + (
            "\n\n## Violations\n\n" + "\n".join(f"- {json.dumps(item, ensure_ascii=False)}" for item in outcome.violations)
            if outcome.violations
            else ""
        )
        + "\n\n## Full Report\n\n"
        + outcome.report
        + "\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def save_review_summary(
    reports_root: Path,
    episode: str,
    stage: str,
    round_index: int,
    business: ReviewOutcome,
    compliance: ReviewOutcome,
) -> Path:
    recommendation = build_recommendation(business, compliance)
    payload: dict[str, Any] = {
        "episode": episode,
        "stage": stage,
        "round": round_index,
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "business": {
            "result": business.result,
            "average_score": business.average_score,
            "has_item_below_6": business.has_item_below_6,
            "dimension_scores": business.dimension_scores,
            "issues": business.issues,
            "report_path": str(reports_root / "reviews" / episode / stage / f"round-{round_index:02d}-business.md"),
        },
        "compliance": {
            "result": compliance.result,
            "issues": compliance.issues,
            "violations": compliance.violations,
            "report_path": str(reports_root / "reviews" / episode / stage / f"round-{round_index:02d}-compliance.md"),
        },
        "recommendation": recommendation,
    }
    path = reports_root / "reviews" / episode / stage / "summary.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_review_summary(reports_root: Path, episode: str, stage: str) -> dict[str, Any]:
    path = reports_root / "reviews" / episode / stage / "summary.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_recommendation(business: ReviewOutcome, compliance: ReviewOutcome) -> str:
    if compliance.result != "PASS":
        return "manual_reject_candidate"
    if business.result != "PASS":
        if business.average_score is not None and business.average_score >= 8 and business.has_item_below_6 is False:
            return "manual_accept_candidate"
        return "manual_reject_candidate"
    if business.average_score is None or business.has_item_below_6 is None:
        return "manual_review_required"
    if business.average_score >= 8 and business.has_item_below_6 is False:
        return "auto_accept"
    return "manual_reject_candidate"
