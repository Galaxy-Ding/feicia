from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.asset_registry import load_asset_registry
from feicai_seedance.llm_client import MockLLMClient
from feicai_seedance.pipeline import Pipeline


class FlakyMockLLMClient(MockLLMClient):
    def __init__(self) -> None:
        super().__init__()
        self.first_call = True

    def chat(self, model, messages):  # type: ignore[override]
        if self.first_call:
            self.first_call = False
            raise RuntimeError("temporary failure")
        return super().chat(model, messages)


class HistorySpyMockLLMClient(MockLLMClient):
    def __init__(self) -> None:
        super().__init__()
        self.message_history: list[list[dict[str, str]]] = []

    def chat(self, model, messages):  # type: ignore[override]
        self.message_history.append([dict(item) for item in messages])
        return super().chat(model, messages)


class TestPipelineIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        source_root = Path(__file__).resolve().parents[1]
        for name in ["agents", "skills", "CLAUDE.md", "project-config.json"]:
            src = source_root / name
            dst = self.root / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        (self.root / "script").mkdir(parents=True, exist_ok=True)
        (self.root / "script" / "ep01-demo.md").write_text("林书白深夜在住处翻书。", encoding="utf-8")
        self.pipeline = Pipeline(self.root, llm_client=MockLLMClient())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_full_pipeline(self) -> None:
        self.pipeline.run_start("ep01")
        self.pipeline.run_review("ep01", "director")
        self.pipeline.run_accept("ep01", "director")
        self.pipeline.run_design("ep01")
        self.pipeline.run_review("ep01", "design")
        self.pipeline.run_accept("ep01", "design")
        registry = load_asset_registry(self.root)
        image_source = self.root / "seed.png"
        image_source.write_bytes(b"fakepng")
        for asset in registry["assets"]:
            if asset["asset_type"] in {"character", "scene_panel"}:
                self.pipeline.run_register_image("ep01", asset["asset_id"], str(image_source))
        self.pipeline.run_build_reference_map("ep01")
        self.pipeline.run_prompt("ep01")
        self.pipeline.run_review("ep01", "prompt")
        self.pipeline.run_accept("ep01", "prompt")

        self.assertTrue((self.root / "outputs" / "ep01" / "01-director-analysis.md").exists())
        self.assertTrue((self.root / "outputs" / "ep01" / "01-director-analysis.json").exists())
        self.assertTrue((self.root / "assets" / "character-prompts.md").exists())
        self.assertTrue((self.root / "assets" / "scene-prompts.md").exists())
        self.assertTrue((self.root / "outputs" / "ep01" / "02-seedance-prompts.md").exists())
        self.assertTrue((self.root / "outputs" / "ep01" / "02-seedance-prompts.json").exists())
        self.assertTrue((self.root / "outputs" / "ep01" / "validation" / "director-validation.json").exists())
        self.assertTrue((self.root / "outputs" / "ep01" / "validation" / "design-validation.json").exists())
        self.assertTrue((self.root / "outputs" / "ep01" / "validation" / "prompt-validation.json").exists())
        self.assertTrue((self.root / "reports" / "assessments" / "ep01" / "overview.md").exists())

    def test_status_and_help(self) -> None:
        self.assertIn("项目进度", self.pipeline.status_report())
        self.assertIn("review <ep01> <director|design|prompt|all>", self.pipeline.command_help())

    def test_logs_created(self) -> None:
        self.pipeline.run_start("ep01")
        self.assertTrue((self.root / "logs" / "run-log.jsonl").exists())
        self.assertTrue((self.root / "logs" / "review-log.jsonl").exists())

    def test_retry_path(self) -> None:
        pipeline = Pipeline(self.root, llm_client=FlakyMockLLMClient())
        result = pipeline.run_start("ep01")
        self.assertIn("已自动通过审核并完成", result)

    def test_revise_storyboard(self) -> None:
        self.pipeline.run_start("ep01")
        self.pipeline.run_accept("ep01", "director")
        self.pipeline.run_design("ep01")
        self.pipeline.run_accept("ep01", "design")
        registry = load_asset_registry(self.root)
        image_source = self.root / "seed.png"
        image_source.write_bytes(b"fakepng")
        for asset in registry["assets"]:
            if asset["asset_type"] in {"character", "scene_panel"}:
                self.pipeline.run_register_image("ep01", asset["asset_id"], str(image_source))
        self.pipeline.run_build_reference_map("ep01")
        self.pipeline.run_prompt("ep01")
        self.pipeline.run_accept("ep01", "prompt")
        result = self.pipeline.run_revise("ep01", "storyboard", "请加强环境音描述")
        self.assertIn("已修订分镜文件", result)

    def test_manual_accept_flow(self) -> None:
        self.pipeline.run_start("ep01")
        result = self.pipeline.run_accept("ep01", "director")
        self.assertIn("已人工放行", result)
        self.assertIn("assessment_report", result)

    def test_review_flow(self) -> None:
        self.pipeline.run_start("ep01")
        result = self.pipeline.run_review("ep01", "director")
        self.assertIn("审核报告已生成", result)
        self.assertTrue((self.root / "reports" / "assessments" / "ep01" / "director.md").exists())
        summary = json.loads((self.root / "reports" / "reviews" / "ep01" / "director" / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["business"]["average_score"], 8.6)
        self.assertFalse(summary["business"]["has_item_below_6"])

    def test_mixed_provider_routing(self) -> None:
        llm = MockLLMClient()
        pipeline = Pipeline(self.root, llm_client=llm)

        pipeline.run_start("ep01")
        start_providers = {(call["model"], call["provider"]) for call in llm.calls}
        self.assertIn(("gpt-5.4", "codex"), start_providers)
        self.assertIn(("gpt-5.4", "claude"), start_providers)

        llm.calls.clear()
        pipeline.run_accept("ep01", "director")
        pipeline.run_design("ep01")
        design_providers = {call["provider"] for call in llm.calls}
        self.assertIn("claude", design_providers)

    def test_registry_bootstrap_on_pipeline_init(self) -> None:
        self.assertTrue((self.root / "assets" / "registry" / "asset-registry.json").exists())
        self.assertTrue((self.root / "assets" / "registry" / "character-index.json").exists())
        self.assertTrue((self.root / "assets" / "registry" / "scene-index.json").exists())

    def test_prompt_requires_reference_map(self) -> None:
        self.pipeline.run_start("ep01")
        self.pipeline.run_accept("ep01", "director")
        self.pipeline.run_design("ep01")
        self.pipeline.run_accept("ep01", "design")
        with self.assertRaises(RuntimeError):
            self.pipeline.run_prompt("ep01")

    def test_session_history_is_reused_for_revision(self) -> None:
        llm = HistorySpyMockLLMClient()
        pipeline = Pipeline(self.root, llm_client=llm)
        pipeline.run_start("ep01")
        pipeline.run_revise("ep01", "director", "请强化动作链")
        revision_call = next(
            messages for messages in reversed(llm.message_history) if messages[-1]["content"].startswith("你需要修订当前阶段一产物")
        )
        joined_history = "\n".join(item["content"] for item in revision_call[:-1])
        self.assertIn("# 导演讲戏本", joined_history)


if __name__ == "__main__":
    unittest.main()
