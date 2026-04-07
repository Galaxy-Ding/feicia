from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.acceptance_runner import generate_acceptance_evidence
from feicai_seedance.asset_registry import load_asset_registry
from feicai_seedance.llm_client import MockLLMClient
from feicai_seedance.pipeline import Pipeline


class TestAcceptanceEvidence(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        source_root = Path(__file__).resolve().parents[1]
        prompt_assets_root = source_root if (source_root / "agents").exists() else source_root.parent / "0-origin_document"
        for name in ["agents", "skills", "CLAUDE.md"]:
            src = prompt_assets_root / name
            dst = self.root / name
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        shutil.copy2(source_root / "project-config.json", self.root / "project-config.json")
        (self.root / "script").mkdir(parents=True, exist_ok=True)
        (self.root / "script" / "ep01-demo.md").write_text("镜头脚本示例", encoding="utf-8")
        self.pipeline = Pipeline(self.root, llm_client=MockLLMClient())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run_full_pipeline(self) -> None:
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

    def test_acceptance_evidence_detects_missing_sample_assets(self) -> None:
        self._run_full_pipeline()

        payload = generate_acceptance_evidence(self.root, "ep01")

        self.assertEqual(payload["result"], "FAIL")
        self.assertIn("golden_samples_present", payload["missing_items"])
        self.assertIn("variant_samples_present", payload["missing_items"])

    def test_acceptance_evidence_passes_when_sample_assets_exist(self) -> None:
        self._run_full_pipeline()
        golden_dir = self.root / "assets" / "acceptance" / "ep01" / "golden"
        variant_dir = self.root / "assets" / "acceptance" / "ep01" / "variants"
        golden_dir.mkdir(parents=True, exist_ok=True)
        variant_dir.mkdir(parents=True, exist_ok=True)
        (golden_dir / "golden.png").write_bytes(b"golden")
        (variant_dir / "variant.png").write_bytes(b"variant")

        payload = generate_acceptance_evidence(self.root, "ep01")

        self.assertEqual(payload["result"], "PASS")
        self.assertTrue(Path(payload["markdown_path"]).exists())
        self.assertTrue(Path(payload["json_path"]).exists())


if __name__ == "__main__":
    unittest.main()
