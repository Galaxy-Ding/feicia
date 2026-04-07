from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.structured_protocols import (
    build_design_validation,
    build_director_validation,
    build_seedance_validation,
    can_auto_accept_review,
    ensure_asset_registry_files,
    parse_business_review_payload,
    parse_compliance_review_payload,
    parse_director_markdown,
    parse_seedance_markdown,
)


class TestStructuredProtocols(unittest.TestCase):
    def test_parse_director_markdown_three_random_cases(self) -> None:
        for index in range(3):
            duration = random.randint(6, 10)
            artifact = (
                "# 导演讲戏本\n\n"
                f"## P0{index + 1} 开场{index}\n\n"
                "- 人物：角色A、角色B\n"
                "- 场景：旧屋客厅\n"
                "- 镜头组：单镜头\n"
                f"- 时长建议：{duration}s\n\n"
                "**导演阐述**：角色A推门进入房间，角色B抬头看向他。"
                "镜头从门口缓慢推近到两人的侧脸。冷白台灯和窗外月光一起压住桌面。\n\n"
                "## 人物清单\n\n| 人物 | 年龄 | 外观关键词 | 素材状态 |\n|---|---|---|---|\n| 角色A | 20 | 黑发 | 新增 |\n| 角色B | 22 | 短发 | 新增 |\n\n"
                "## 场景清单\n\n| 场景 | 时间 | 光线/色调 | 氛围关键词 | 素材状态 |\n|---|---|---|---|---|\n| 旧屋客厅 | 夜 | 冷白台灯、月光 | 压抑 | 新增 |\n"
            )
            with self.subTest(index=index):
                payload = parse_director_markdown("ep01", artifact)
                validation = build_director_validation(payload)
                self.assertEqual(payload["episode"], "ep01")
                self.assertEqual(len(payload["plot_points"]), 1)
                self.assertEqual(validation["result"], "PASS")

    def test_director_validation_negative_cases(self) -> None:
        cases = [
            (
                "只有抽象情绪",
                "**导演阐述**：他感到悲伤而孤独。",
                "DIRECTOR_ABSTRACT_ONLY",
            ),
            (
                "缺少运镜",
                "**导演阐述**：他推门进入房间。冷白台灯照着他的肩膀。",
                "DIRECTOR_CAMERA_DIRECTION_MISSING",
            ),
            (
                "缺少光源",
                "**导演阐述**：他推门进入房间。镜头缓慢推近到他的侧脸。",
                "DIRECTOR_LIGHT_SPECIFICITY_MISSING",
            ),
            (
                "节拍过密",
                "**导演阐述**：他推门进入房间。他快步冲向桌边。镜头迅速推近到手部。他抓起电话立刻转身。镜头再跟拍到门口。冷白台灯照着他的肩膀。",
                "DIRECTOR_BEAT_DENSITY_OVERFLOW",
            ),
        ]
        for name, narration, issue_code in cases:
            artifact = (
                "# 导演讲戏本\n\n"
                "## P01 开场\n\n"
                "- 人物：角色A\n"
                "- 场景：旧屋客厅\n"
                "- 镜头组：单镜头\n"
                "- 时长建议：8s\n\n"
                f"{narration}\n\n"
                "## 人物清单\n\n| 人物 | 年龄 | 外观关键词 | 素材状态 |\n|---|---|---|---|\n| 角色A | 20 | 黑发 | 新增 |\n\n"
                "## 场景清单\n\n| 场景 | 时间 | 光线/色调 | 氛围关键词 | 素材状态 |\n|---|---|---|---|---|\n| 旧屋客厅 | 夜 | 冷白台灯 | 压抑 | 新增 |\n"
            )
            with self.subTest(name=name):
                payload = parse_director_markdown("ep01", artifact)
                validation = build_director_validation(payload)
                issue_codes = {item["code"] for item in validation["issues"]}
                self.assertIn(issue_code, issue_codes)

    def test_parse_seedance_markdown_three_random_cases(self) -> None:
        for index in range(3):
            refs = [f"@图片{i}" for i in range(1, random.randint(2, 4))]
            table = "\n".join(f"| {ref} | 人物参考 | 角色{idx} |" for idx, ref in enumerate(refs, start=1))
            prompt_refs = "、".join(refs)
            artifact = (
                "## 素材对应表\n\n| 引用编号 | 素材类型 | 对应素材 |\n|---|---|---|\n"
                f"{table}\n\n"
                f"## P0{index + 1} 开场\n\n"
                f"**Seedance 2.0 提示词**：使用{prompt_refs}完成画面，镜头缓慢推近，保留风声和脚步声。\n"
            )
            with self.subTest(index=index):
                payload = parse_seedance_markdown("ep01", artifact)
                validation = build_seedance_validation(payload)
                self.assertEqual(payload["episode"], "ep01")
                self.assertEqual(validation["result"], "PASS")

    def test_seedance_validation_negative_cases(self) -> None:
        too_many_refs = "".join(f"@图片{i}" for i in range(1, 11))
        artifact = (
            "## 素材对应表\n\n| 引用编号 | 素材类型 | 对应素材 |\n|---|---|---|\n| @图片1 | 人物参考 | 角色A |\n\n"
            "## P01 开场\n\n"
            f"**Seedance 2.0 提示词**：使用{too_many_refs}完成画面，镜头缓慢推近。\n"
        )
        payload = parse_seedance_markdown("ep01", artifact)
        validation = build_seedance_validation(payload)
        issue_codes = {item["code"] for item in validation["issues"]}
        self.assertIn("SEEDANCE_IMAGE_REFERENCE_OVER_LIMIT", issue_codes)
        self.assertIn("SEEDANCE_AUDIO_DESIGN_MISSING", issue_codes)

    def test_seedance_grid_and_safe_zone_negative_cases(self) -> None:
        artifact = (
            "## 素材对应表\n\n| 引用编号 | 素材类型 | 对应素材 |\n|---|---|---|\n| @图片1 | 场景参考 | 场景宫格 |\n\n"
            "## P01 开场\n\n"
            "**Seedance 2.0 提示词**：使用@图片1这张九宫格完成画面，8秒内一开场就推门、冲刺、抓起电话、转身、再冲向门口，最后一秒突然喊出台词。\n"
        )
        payload = parse_seedance_markdown("ep01", artifact)
        validation = build_seedance_validation(payload)
        issue_codes = {item["code"] for item in validation["issues"]}
        self.assertIn("SEEDANCE_SCENE_GRID_USED_DIRECTLY", issue_codes)
        self.assertIn("SEEDANCE_SAFE_ZONE_RISK", issue_codes)
        self.assertIn("SEEDANCE_BEAT_DENSITY_OVERFLOW", issue_codes)

    def test_design_validation_grid_spec_cases(self) -> None:
        character_content = "# 人物提示词\n\n**出图要求**：一张图\n\n**提示词**：角色设定。"
        valid_scene = (
            "# 场景道具提示词\n\n"
            "请生成一张 3x4 宫格布局的电影场景环境图像。\n\n"
            "### 视觉规范\n整体风格：写实\n\n"
            "### Panel Breakdown\n\n"
            "格1——【场景1】\n格2——【场景2】\n格3——【场景3】\n格4——【场景4】\n"
            "格5——【场景5】\n格6——【场景6】\n格7——【场景7】\n格8——【场景8】\n"
            "格9——【场景9】\n格10——【场景10】\n"
        )
        invalid_scene = valid_scene.replace("3x4", "3x3", 1)
        valid_result = build_design_validation(character_content, valid_scene)
        invalid_result = build_design_validation(character_content, invalid_scene)
        self.assertEqual(valid_result["result"], "PASS")
        self.assertEqual(invalid_result["result"], "FAIL")
        issue_codes = {item["code"] for item in invalid_result["issues"]}
        self.assertIn("DESIGN_GRID_SPEC_MISMATCH", issue_codes)

    def test_review_payload_parsers_and_gate(self) -> None:
        business = parse_business_review_payload(
            {
                "result": "PASS",
                "average_score": 8.2,
                "has_item_below_6": False,
                "dimension_scores": {"fidelity": 8.1, "visual_clarity": 8.3, "audio_design": 8.2},
                "issues": [],
                "report": "业务审核通过",
            }
        )
        compliance = parse_compliance_review_payload(
            {
                "result": "PASS",
                "violations": [],
                "issues": [],
                "report": "合规审核通过",
            }
        )
        self.assertTrue(can_auto_accept_review(business, compliance))

    def test_asset_registry_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            assets_root = Path(temp_dir) / "assets"
            ensure_asset_registry_files(assets_root)
            registry_payload = json.loads((assets_root / "registry" / "asset-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry_payload["assets"], [])
            self.assertTrue((assets_root / "library" / "characters").exists())
            self.assertTrue((assets_root / "manifests" / "image-generation-log.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
