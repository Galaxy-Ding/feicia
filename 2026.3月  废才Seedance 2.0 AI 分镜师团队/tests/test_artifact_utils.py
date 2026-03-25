from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from feicai_seedance.artifact_utils import (
    append_markdown,
    split_art_design_artifact,
    validate_character_asset,
    validate_director_artifact,
    validate_scene_asset,
    validate_seedance_artifact,
)


class TestArtifactUtils(unittest.TestCase):
    def test_split_art_design_artifact_three_cases(self) -> None:
        for index in range(3):
            artifact = (
                "# 人物提示词\n\n"
                f"## 角色{index}\n\n**出图要求**：一张图\n\n**提示词**：内容{random.randint(1, 999)}\n\n"
                "---\n\n# 场景道具提示词\n\n"
                "### 视觉规范\nA\n\n### Panel Breakdown\nB\n"
            )
            with self.subTest(index=index):
                character, scene = split_art_design_artifact(artifact)
                self.assertIn("# 人物提示词", character)
                self.assertIn("# 场景道具提示词", scene)

    def test_append_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "a.md"
            append_markdown(path, "# A")
            append_markdown(path, "# B")
            text = path.read_text(encoding="utf-8")
            self.assertIn("# A", text)
            self.assertIn("# B", text)
            self.assertIn("---", text)

    def test_validators(self) -> None:
        validate_director_artifact(
            "# 导演讲戏本\n\n"
            "## P01 开场\n\n"
            "- 人物：角色A\n"
            "- 场景：场景A\n"
            "- 镜头组：单镜头\n"
            "- 时长建议：8s\n\n"
            "**导演阐述**：角色A推门进入房间。镜头从门口缓慢推近到他的侧脸。冷白台灯压在他的肩上。\n\n"
            "## 人物清单\n\n| 人物 | 年龄 | 外观关键词 | 素材状态 |\n|---|---|---|---|\n| 角色A | 20 | 黑发 | 新增 |\n\n"
            "## 场景清单\n\n| 场景 | 时间 | 光线/色调 | 氛围关键词 | 素材状态 |\n|---|---|---|---|---|\n| 场景A | 夜 | 冷白台灯 | 压抑 | 新增 |\n"
        )
        validate_character_asset("# 人物提示词\n\n**出图要求**：x\n\n**提示词**：y")
        validate_scene_asset("# 场景道具提示词\n\n### 视觉规范\nx\n\n### Panel Breakdown\ny")
        validate_seedance_artifact(
            "## 素材对应表\n\n| 引用编号 | 素材类型 | 对应素材 |\n|---|---|---|\n| @图片1 | 人物参考 | 角色A |\n\n"
            "## P01 开场\n\n**Seedance 2.0 提示词**：使用@图片1，镜头缓慢推近，环境里保留风声。\n"
        )


if __name__ == "__main__":
    unittest.main()
