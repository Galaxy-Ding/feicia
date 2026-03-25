from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.acceptance_store import get_stage_status, load_acceptance_state, save_stage_acceptance
from feicai_seedance.assessment_store import (
    extract_highlights,
    quality_band,
    recommendation_label,
    save_episode_assessment_overview,
    save_stage_assessment_report,
)
from feicai_seedance.models import ReviewOutcome
from feicai_seedance.review_store import build_recommendation, load_review_summary, save_review_round, save_review_summary


class TestAcceptanceAndReviews(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.reports_root = self.root / "reports"
        self.reports_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_acceptance_roundtrip(self) -> None:
        save_stage_acceptance(self.reports_root, "ep01", "director", "accepted", "manual", {"recommendation": "manual_accept_candidate"})
        state = load_acceptance_state(self.reports_root, "ep01")
        self.assertEqual(state["stages"]["director"]["status"], "accepted")
        self.assertEqual(get_stage_status(self.reports_root, "ep01", "director"), "accepted")

    def test_review_summary_roundtrip(self) -> None:
        business = ReviewOutcome(
            "FAIL",
            "业务审核未通过",
            ["a", "b"],
            average_score=8.1,
            has_item_below_6=False,
            dimension_scores={"fidelity": 8.0, "visual_clarity": 7.6},
        )
        compliance = ReviewOutcome("PASS", "合规审核：PASS", [])
        save_review_round(self.reports_root, "ep01", "director", 1, "business", business)
        save_review_round(self.reports_root, "ep01", "director", 1, "compliance", compliance)
        save_review_summary(self.reports_root, "ep01", "director", 1, business, compliance)
        summary = load_review_summary(self.reports_root, "ep01", "director")
        self.assertEqual(summary["business"]["average_score"], 8.1)
        self.assertEqual(summary["recommendation"], "manual_accept_candidate")

    def test_score_and_recommendation(self) -> None:
        business_pass = ReviewOutcome("PASS", "ok", average_score=8.4, has_item_below_6=False)
        business_soft_fail = ReviewOutcome("FAIL", "needs work", average_score=8.1, has_item_below_6=False)
        business_hard_fail = ReviewOutcome("FAIL", "needs work", average_score=7.6, has_item_below_6=True)
        compliance_pass = ReviewOutcome("PASS", "ok")
        compliance_fail = ReviewOutcome("FAIL", "blocked")

        self.assertEqual(build_recommendation(business_pass, compliance_pass), "auto_accept")
        self.assertEqual(build_recommendation(business_soft_fail, compliance_pass), "manual_accept_candidate")
        self.assertEqual(build_recommendation(business_hard_fail, compliance_fail), "manual_reject_candidate")

    def test_quality_band_with_random_cases(self) -> None:
        cases = [
            (random.uniform(9.0, 9.8), "优秀"),
            (random.uniform(8.0, 8.9), "良好"),
            (random.uniform(7.5, 7.9), "可用"),
        ]
        for score, expected_prefix in cases:
            with self.subTest(score=score):
                self.assertIn(expected_prefix, quality_band(score))

    def test_extract_highlights_with_random_cases(self) -> None:
        positive_lines = random.sample(
            [
                "整体完成度高，镜头语言清晰。",
                "基本通过，人物关系成立。",
                "收束有力，结尾呼应良好。",
                "覆盖完整，风格统一。",
            ],
            k=3,
        )
        report = "\n".join(["# report", "| table | skip |", *positive_lines, "需要修改：补充动作细节。"])
        highlights = extract_highlights(report, limit=3)
        self.assertEqual(len(highlights), 3)
        for line in positive_lines:
            with self.subTest(line=line):
                self.assertIn(line, highlights)

    def test_recommendation_label(self) -> None:
        self.assertEqual(recommendation_label("auto_accept"), "可自动放行")
        self.assertEqual(recommendation_label("manual_accept_candidate"), "建议人工复核后放行")
        self.assertEqual(recommendation_label("manual_reject_candidate"), "建议先修改后再审")

    def test_assessment_report_roundtrip(self) -> None:
        business = ReviewOutcome(
            "FAIL",
            "整体完成度高，但关键链路仍需补强。\n收束有力，首尾呼应良好。",
            ["问题1：关键桥段解释偏多", "问题2：时间链仍需补强"],
            average_score=8.2,
            has_item_below_6=False,
            dimension_scores={"fidelity": 8.2, "visual_clarity": 8.1, "action_executability": 8.0},
        )
        compliance = ReviewOutcome("PASS", "合规审核：PASS", [])
        save_review_round(self.reports_root, "ep01", "director", 1, "business", business)
        save_review_round(self.reports_root, "ep01", "director", 1, "compliance", compliance)
        save_review_summary(self.reports_root, "ep01", "director", 1, business, compliance)
        save_stage_acceptance(self.reports_root, "ep01", "director", "pending", "system", notes="waiting")

        report_path = save_stage_assessment_report(self.reports_root, "ep01", "director")
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("人工审核决策报告", content)
        self.assertIn("建议人工复核后放行", content)
        self.assertIn("python -m feicai_seedance.cli accept ep01 director", content)

    def test_episode_assessment_overview_roundtrip(self) -> None:
        business = ReviewOutcome(
            "PASS",
            "基本通过。",
            [],
            average_score=8.8,
            has_item_below_6=False,
            dimension_scores={"fidelity": 8.8, "visual_clarity": 8.8},
        )
        compliance = ReviewOutcome("PASS", "合规审核：PASS", [])
        save_review_round(self.reports_root, "ep01", "director", 1, "business", business)
        save_review_round(self.reports_root, "ep01", "director", 1, "compliance", compliance)
        save_review_summary(self.reports_root, "ep01", "director", 1, business, compliance)
        save_stage_acceptance(self.reports_root, "ep01", "director", "accepted", "auto")
        save_stage_assessment_report(self.reports_root, "ep01", "director")

        overview_path = save_episode_assessment_overview(self.reports_root, "ep01", ["director"])
        self.assertTrue(overview_path.exists())
        self.assertIn("director", overview_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
