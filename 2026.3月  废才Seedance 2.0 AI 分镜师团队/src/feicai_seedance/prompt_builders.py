from __future__ import annotations

from pathlib import Path

from .models import ProjectConfig
from .prompt_loader import PromptBundle


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_director_generation_prompt(
    config: ProjectConfig,
    prompts: PromptBundle,
    episode: str,
    script_text: str,
) -> list[dict[str, str]]:
    system = "\n\n".join(
        [
            prompts.orchestrator,
            prompts.agent_prompts["director"],
            prompts.skill_prompts["director-skill"],
            prompts.template_prompts["director-analysis-template"],
        ]
    )
    user = (
        f"你正在执行阶段一：导演分析。\n"
        f"项目风格：{config.visual_style}\n"
        f"目标媒介：{config.target_media}\n"
        f"目标集数：{episode}\n\n"
        "请严格根据模板生成完整 Markdown，直接输出最终文件内容，不要解释。\n\n"
        f"剧本内容如下：\n\n{script_text}\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_art_generation_prompt(
    config: ProjectConfig,
    prompts: PromptBundle,
    episode: str,
    director_analysis: str,
    character_assets: str,
    scene_assets: str,
) -> list[dict[str, str]]:
    system = "\n\n".join(
        [
            prompts.orchestrator,
            prompts.agent_prompts["art-designer"],
            prompts.skill_prompts["art-design-skill"],
            prompts.skill_prompts["gemini-image-prompt-guide"],
            prompts.extra_prompts["character-examples"],
            prompts.extra_prompts["scene-examples"],
            prompts.template_prompts["art-design-template"],
        ]
    )
    user = (
        f"你正在执行阶段二：服化道设计。\n"
        f"目标集数：{episode}\n"
        "请直接输出完整 Markdown 内容，内容需同时覆盖人物提示词和场景道具提示词，便于程序拆分写入。\n\n"
        f"导演分析文件：\n\n{director_analysis}\n\n"
        f"已有人物资产：\n\n{character_assets or '（暂无）'}\n\n"
        f"已有场景资产：\n\n{scene_assets or '（暂无）'}\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_storyboard_generation_prompt(
    prompts: PromptBundle,
    episode: str,
    director_analysis: str,
    ready_assets_summary: str,
    reference_map_text: str,
) -> list[dict[str, str]]:
    system = "\n\n".join(
        [
            prompts.orchestrator,
            prompts.agent_prompts["storyboard-artist"],
            prompts.skill_prompts["seedance-storyboard-skill"],
            prompts.skill_prompts["seedance-prompt-methodology"],
            prompts.extra_prompts["seedance-examples"],
            prompts.template_prompts["seedance-prompts-template"],
        ]
    )
    user = (
        f"你正在执行阶段三：Seedance 2.0 分镜编写。\n"
        f"目标集数：{episode}\n"
        "请严格基于已登记图片资产和 reference-map 输出最终 Markdown 文件内容，不要加解释。\n\n"
        f"导演分析：\n\n{director_analysis}\n\n"
        f"可引用图片资产摘要：\n\n{ready_assets_summary}\n\n"
        f"reference-map.json：\n\n{reference_map_text}\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_review_prompt(
    prompts: PromptBundle,
    stage_name: str,
    review_skill_key: str,
    artifact_text: str,
    upstream_context: str,
) -> list[dict[str, str]]:
    system = "\n\n".join(
        [
            prompts.orchestrator,
            prompts.agent_prompts["director"],
            prompts.skill_prompts[review_skill_key],
        ]
    )
    user = (
        f"你正在执行{stage_name}的业务审核。"
        "返回严格 JSON 审核结果，格式为"
        '{"result":"PASS|FAIL","average_score":8.2,"has_item_below_6":false,'
        '"dimension_scores":{"fidelity":8,"visual_clarity":8,"action_executability":8,"camera_executability":8,"audio_design":8,"emotion_accuracy":8},'
        '"issues":[{"id":"ISSUE-001","severity":"high","location":"P01","problem":"问题描述","fix_direction":"修改方向"}],'
        '"report":"完整审核报告"}。'
        "不要输出 JSON 之外的任何内容。\n\n"
        f"上游上下文：\n{upstream_context}\n\n"
        f"待审核内容：\n{artifact_text}\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_compliance_prompt(
    prompts: PromptBundle,
    stage_name: str,
    artifact_text: str,
) -> list[dict[str, str]]:
    system = "\n\n".join(
        [
            prompts.orchestrator,
            prompts.agent_prompts["director"],
            prompts.skill_prompts["compliance-review-skill"],
        ]
    )
    user = (
        f"你正在执行{stage_name}的合规审核。"
        "返回严格 JSON 审核结果，格式为"
        '{"result":"PASS|FAIL","violations":[{"rule_id":"RULE-001","severity":"high","location":"P01","detail":"违规描述"}],'
        '"issues":[{"id":"ISSUE-001","severity":"high","location":"P01","problem":"问题描述","fix_direction":"修改方向"}],'
        '"report":"完整审核报告"}。'
        "不要输出 JSON 之外的任何内容。\n\n"
        f"待审核内容：\n{artifact_text}\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_revision_prompt(stage_name: str, artifact_text: str, issues: list[str]) -> list[dict[str, str]]:
    prompt = (
        f"你需要修订当前{stage_name}产物。请根据以下问题一次性修完，并直接输出修订后的完整 Markdown 文件内容，不要解释。\n\n"
        f"现有内容：\n{artifact_text}\n\n"
        f"问题列表：\n- " + "\n- ".join(issues)
    )
    return [{"role": "user", "content": prompt}]
