from __future__ import annotations

import json
from pathlib import Path

from .asset_registry import (
    build_reference_map,
    load_reference_map,
    ready_asset_summary,
    register_asset_image,
    sync_design_assets,
)
from .assessment_store import (
    build_stage_assessment_snapshot,
    save_episode_assessment_overview,
    save_stage_assessment_report,
)
from .acceptance_store import get_stage_status, save_stage_acceptance
from .acceptance_runner import generate_acceptance_evidence
from .artifact_utils import (
    has_episode_block,
    read_episode_block,
    split_art_design_artifact,
    upsert_episode_block,
    validate_character_asset,
    validate_director_artifact,
    validate_scene_asset,
    validate_seedance_artifact,
)
from .character_pipeline import CharacterPipeline
from .config import ensure_runtime_directories, load_config
from .llm_client import LLMClient, RoutedOpenAICompatibleClient
from .logging_utils import append_jsonl
from .models import ProjectConfig, ReviewOutcome
from .prompt_builders import (
    build_art_generation_prompt,
    build_compliance_prompt,
    build_director_generation_prompt,
    build_revision_prompt,
    build_review_prompt,
    build_storyboard_generation_prompt,
    read_optional,
)
from .prompt_loader import PromptLoader
from .review_store import load_review_summary, save_review_round, save_review_summary
from .scene_pipeline import ScenePipeline
from .sessions import SessionStore
from .status import detect_all_statuses, find_script_files, pick_default_episode
from .structured_protocols import (
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
from .utils import extract_json_object, merge_issue_lists, sanitize_episode_id


class Pipeline:
    def __init__(self, project_root: Path, llm_client: LLMClient | None = None) -> None:
        self.project_root = project_root.resolve()
        self.config: ProjectConfig = load_config(self.project_root)
        ensure_runtime_directories(self.config)
        ensure_asset_registry_files(self.config.paths.assets)
        self.character_pipeline = CharacterPipeline(self.project_root)
        self.scene_pipeline = ScenePipeline(self.project_root)
        self.prompts = None
        self.sessions = SessionStore(self.project_root, self.config.paths.sessions)
        self.llm = llm_client or RoutedOpenAICompatibleClient(self.config.providers)

    def status_report(self) -> str:
        statuses = detect_all_statuses(self.config)
        if not statuses:
            return "未检测到剧本文件。请先将剧本放入 script/ 目录。"
        current_episode = pick_default_episode(statuses)
        lines = ["项目进度：", ""]
        for item in statuses:
            lines.append(f"- {item.episode}: {item.stage}")
        lines.append("")
        lines.append(f"当前默认集数：{current_episode}")
        return "\n".join(lines)

    def run_start(self, episode: str | None = None) -> str:
        target = self._resolve_episode(episode)
        script_file = self._get_script_file(target)
        script_text = script_file.read_text(encoding="utf-8")
        session = self.sessions.get_or_create(target, "director")
        messages = build_director_generation_prompt(self.config, self._get_prompts(), target, script_text)
        artifact = self._chat("director_generate", self._with_session_history(session, messages))
        self.sessions.append_history(session, messages + [{"role": "assistant", "content": artifact}])
        artifact, accepted = self._review_and_revise(
            target,
            stage_name="阶段一",
            stage_key="director",
            role="director",
            artifact=artifact,
            business_skill="script-analysis-review-skill",
            upstream_context=script_text,
            revision_model_key="director_generate",
            validator=validate_director_artifact,
        )

        output_dir = self.config.paths.outputs / target
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "01-director-analysis.md"
        director_json_path = output_dir / "01-director-analysis.json"
        validation_path = output_dir / "validation" / "director-validation.json"
        director_json = parse_director_markdown(target, artifact)
        director_validation = build_director_validation(director_json)
        output_path.write_text(artifact, encoding="utf-8")
        director_json_path.write_text(self._dump_json(director_json), encoding="utf-8")
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(self._dump_json(director_validation), encoding="utf-8")
        self._log_run(target, "DIRECTOR_ANALYSIS", "SUCCESS", str(output_path))
        return self._stage_result_message(target, "director", output_path, accepted)

    def run_design(self, episode: str | None = None) -> str:
        target = self._resolve_episode(episode)
        if get_stage_status(self.config.paths.reports, target, "director") != "accepted":
            raise RuntimeError("阶段一尚未通过或人工放行，请先执行 accept director。")
        director_file = self.config.paths.outputs / target / "01-director-analysis.md"
        if not director_file.exists():
            raise RuntimeError(f"缺少导演分析文件：{director_file}")

        director_analysis = director_file.read_text(encoding="utf-8")
        character_assets = read_optional(self.config.paths.assets / "character-prompts.md")
        scene_assets = read_optional(self.config.paths.assets / "scene-prompts.md")
        session = self.sessions.get_or_create(target, "art-designer")
        messages = build_art_generation_prompt(
            self.config,
            self._get_prompts(),
            target,
            director_analysis,
            character_assets,
            scene_assets,
        )
        artifact = self._chat("art_designer", self._with_session_history(session, messages))
        self.sessions.append_history(session, messages + [{"role": "assistant", "content": artifact}])
        artifact, accepted = self._review_and_revise(
            target,
            stage_name="阶段二",
            stage_key="design",
            role="art-designer",
            artifact=artifact,
            business_skill="art-direction-review-skill",
            upstream_context=director_analysis,
            revision_model_key="art_designer",
            validator=self._validate_art_design_artifact,
        )

        character_content, scene_content = split_art_design_artifact(artifact)
        validate_character_asset(character_content)
        validate_scene_asset(scene_content)
        character_path = self.config.paths.assets / "character-prompts.md"
        scene_path = self.config.paths.assets / "scene-prompts.md"
        upsert_episode_block(character_path, target, "CHARACTER", character_content)
        upsert_episode_block(scene_path, target, "SCENE", scene_content)
        sync_design_assets(self.project_root, target, character_content, scene_content)
        validation_path = self.config.paths.outputs / target / "validation" / "design-validation.json"
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(
            self._dump_json(build_design_validation(character_content, scene_content)),
            encoding="utf-8",
        )
        self._log_run(target, "ART_DESIGN", "SUCCESS", f"{character_path};{scene_path}")
        output_path = Path(f"{character_path};{scene_path}")
        return self._stage_result_message(target, "design", output_path, accepted)

    def run_prompt(self, episode: str | None = None) -> str:
        target = self._resolve_episode(episode)
        if get_stage_status(self.config.paths.reports, target, "design") != "accepted":
            raise RuntimeError("阶段二尚未通过或人工放行，请先执行 accept design。")
        director_file = self.config.paths.outputs / target / "01-director-analysis.md"
        reference_map_path = self.config.paths.outputs / target / "reference-map.json"
        for path in (director_file, reference_map_path):
            if not path.exists():
                raise RuntimeError(f"缺少前置文件：{path}")

        reference_map = load_reference_map(self.project_root, target)
        if not reference_map or not reference_map.get("references"):
            raise RuntimeError("reference-map 不存在可用图片资产，请先登记图片并执行 build-reference-map。")
        if reference_map.get("missing_assets"):
            raise RuntimeError("reference-map 仍存在缺失资产，请先补齐图片登记后重建 reference-map。")

        director_analysis = director_file.read_text(encoding="utf-8")
        session = self.sessions.get_or_create(target, "storyboard-artist")
        messages = build_storyboard_generation_prompt(
            self._get_prompts(),
            target,
            director_analysis,
            ready_asset_summary(self.project_root, target),
            reference_map_path.read_text(encoding="utf-8"),
        )
        artifact = self._chat("storyboard_artist", self._with_session_history(session, messages))
        self.sessions.append_history(session, messages + [{"role": "assistant", "content": artifact}])
        artifact, accepted = self._review_and_revise(
            target,
            stage_name="阶段三",
            stage_key="prompt",
            role="storyboard-artist",
            artifact=artifact,
            business_skill="seedance-prompt-review-skill",
            upstream_context=director_analysis,
            revision_model_key="storyboard_artist",
            validator=validate_seedance_artifact,
        )

        output_dir = self.config.paths.outputs / target
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "02-seedance-prompts.md"
        prompt_json_path = output_dir / "02-seedance-prompts.json"
        validation_path = output_dir / "validation" / "prompt-validation.json"
        prompt_json = parse_seedance_markdown(target, artifact)
        prompt_validation = build_seedance_validation(prompt_json, reference_map)
        output_path.write_text(artifact, encoding="utf-8")
        prompt_json_path.write_text(self._dump_json(prompt_json), encoding="utf-8")
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(self._dump_json(prompt_validation), encoding="utf-8")
        self._log_run(target, "STORYBOARD", "SUCCESS", str(output_path))
        return self._stage_result_message(target, "prompt", output_path, accepted)

    def command_help(self) -> str:
        return (
            "可用命令：\n"
            "- status\n"
            "- start [ep01]\n"
            "- design [ep01]\n"
            "- prompt [ep01]\n"
            "- extract-characters <book_id> <ep01>\n"
            "- build-character-sheets <book_id> <ep01>\n"
            "- export-character-image-tasks <book_id> <ep01>\n"
            "- export-scene-image-tasks <ep01>\n"
            "- generate-character-images <book_id> <ep01> [--browser mock|openclaw]\n"
            "- generate-scene-images <ep01> [--browser mock|openclaw]\n"
            "- review-character-images <book_id> <ep01>\n"
            "- review-scene-images <ep01>\n"
            "- approve-character-assets <book_id> <ep01>\n"
            "- approve-scene-assets <ep01>\n"
            "- export-character-reference-pack <book_id> <ep01>\n"
            "- register-image <ep01> <asset_id> <image_path>\n"
            "- build-reference-map <ep01>\n"
            "- revise <ep01> <director|art|storyboard> <feedback>\n"
            "- review <ep01> <director|design|prompt|all>\n"
            "- accept <ep01> <director|design|prompt|all>\n"
            "- acceptance-evidence <ep01>\n"
            "- help"
        )

    def run_register_image(self, episode: str, asset_id: str, image_path: str) -> str:
        target = sanitize_episode_id(episode)
        asset = register_asset_image(self.project_root, asset_id, image_path)
        self._log_run(target, "REGISTER_ASSET_IMAGE", "SUCCESS", asset["image_path"])
        return (
            f"{target} 已登记图片资产：{asset['asset_id']}\n"
            f"status={asset['status']}\n"
            f"image_path={asset['image_path']}"
        )

    def run_build_reference_map(self, episode: str) -> str:
        target = sanitize_episode_id(episode)
        payload = build_reference_map(self.project_root, target)
        output_path = self.config.paths.outputs / target / "reference-map.json"
        self._log_run(target, "BUILD_REFERENCE_MAP", "SUCCESS", str(output_path))
        return (
            f"{target} reference-map 已生成：{output_path}\n"
            f"references={len(payload.get('references', []))}\n"
            f"missing_assets={len(payload.get('missing_assets', []))}"
        )

    def run_revise(self, episode: str, scope: str, feedback: str) -> str:
        target = sanitize_episode_id(episode)
        if scope == "director":
            return self._revise_director(target, feedback)
        if scope == "art":
            return self._revise_art(target, feedback)
        if scope == "storyboard":
            return self._revise_storyboard(target, feedback)
        raise RuntimeError(f"不支持的 revise scope: {scope}")

    def run_review(self, episode: str, stage: str) -> str:
        target = sanitize_episode_id(episode)
        stages = self._resolve_review_stages(stage)
        outputs: list[str] = []
        for item in stages:
            report_path = save_stage_assessment_report(self.config.paths.reports, target, item)
            snapshot = build_stage_assessment_snapshot(self.config.paths.reports, target, item)
            outputs.append(self._format_review_message(target, item, snapshot, report_path))
        overview_path = save_episode_assessment_overview(self.config.paths.reports, target)
        if len(stages) > 1:
            outputs.append(f"episode_review={overview_path}")
        return "\n\n".join(outputs)

    def run_accept(self, episode: str, stage: str) -> str:
        target = sanitize_episode_id(episode)
        stages = self._resolve_review_stages(stage)
        outputs: list[str] = []
        for item in stages:
            summary = load_review_summary(self.config.paths.reports, target, item)
            if not summary:
                raise RuntimeError(f"No review summary found for {target} {item}")
            assessment_path = save_stage_assessment_report(self.config.paths.reports, target, item)
            save_stage_acceptance(
                self.config.paths.reports,
                target,
                item,
                status="accepted",
                source="manual",
                summary=summary,
                notes=f"Accepted by manual operator command. assessment={assessment_path}",
            )
            outputs.append(self._format_accept_message(target, item, summary, assessment_path))
        overview_path = save_episode_assessment_overview(self.config.paths.reports, target)
        if len(stages) > 1:
            outputs.append(f"episode_review={overview_path}")
        return "\n\n".join(outputs)

    def run_acceptance_evidence(self, episode: str) -> str:
        target = sanitize_episode_id(episode)
        payload = generate_acceptance_evidence(self.project_root, target)
        return (
            f"{target} acceptance evidence generated.\n"
            f"result={payload['result']}\n"
            f"missing_items={len(payload['missing_items'])}\n"
            f"evidence_report={payload['markdown_path']}"
        )

    def run_extract_characters(self, book_id: str, episode: str) -> str:
        payload = self.character_pipeline.extract_characters(book_id, episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-candidate-list.json"
        self._log_run(payload["episode_id"], "EXTRACT_CHARACTERS", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} character candidates 已生成：{output_path}\n"
            f"characters={len(payload.get('characters', []))}\n"
            f"templates={len(payload.get('templates', []))}"
        )

    def run_build_character_sheets(self, book_id: str, episode: str) -> str:
        payload = self.character_pipeline.build_character_sheets(book_id, episode)
        json_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-sheets.json"
        md_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-sheets.md"
        self._log_run(payload["episode_id"], "BUILD_CHARACTER_SHEETS", "SUCCESS", f"{json_path};{md_path}")
        return (
            f"{payload['episode_id']} character sheets 已生成。\n"
            f"json={json_path}\n"
            f"markdown={md_path}\n"
            f"characters={len(payload.get('characters', []))}"
        )

    def run_export_character_image_tasks(self, book_id: str, episode: str) -> str:
        payload = self.character_pipeline.export_character_image_tasks(book_id, episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-image-tasks.json"
        self._log_run(payload["episode_id"], "EXPORT_CHARACTER_IMAGE_TASKS", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} character image tasks 已导出：{output_path}\n"
            f"tasks={len(payload.get('tasks', []))}"
        )

    def run_export_scene_image_tasks(self, episode: str) -> str:
        payload = self.scene_pipeline.export_scene_image_tasks(episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "scenes" / "scene-image-tasks.json"
        self._log_run(payload["episode_id"], "EXPORT_SCENE_IMAGE_TASKS", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} scene image tasks 已导出：{output_path}\n"
            f"tasks={len(payload.get('tasks', []))}\n"
            f"skipped={len(payload.get('skipped_assets', []))}"
        )

    def run_generate_character_images(self, book_id: str, episode: str, browser: str = "mock") -> str:
        payload = self.character_pipeline.generate_character_images(book_id, episode, browser=browser)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-image-run.json"
        self._log_run(payload["episode_id"], "GENERATE_CHARACTER_IMAGES", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} character images 已生成。\n"
            f"browser={payload['browser']}\n"
            f"run_file={output_path}\n"
            f"tasks={len(payload.get('tasks', []))}"
        )

    def run_generate_scene_images(self, episode: str, browser: str = "mock") -> str:
        payload = self.scene_pipeline.generate_scene_images(episode, browser=browser)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "scenes" / "scene-image-run.json"
        self._log_run(payload["episode_id"], "GENERATE_SCENE_IMAGES", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} scene images 已生成。\n"
            f"browser={payload['browser']}\n"
            f"run_file={output_path}\n"
            f"tasks={len(payload.get('tasks', []))}"
        )

    def run_review_character_images(self, book_id: str, episode: str) -> str:
        payload = self.character_pipeline.review_character_images(book_id, episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-review.json"
        passed = sum(1 for item in payload.get("characters", []) if item.get("ready_for_anchor"))
        self._log_run(payload["episode_id"], "REVIEW_CHARACTER_IMAGES", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} character review 已生成。\n"
            f"review_file={output_path}\n"
            f"characters={len(payload.get('characters', []))}\n"
            f"ready_for_anchor={passed}"
        )

    def run_review_scene_images(self, episode: str) -> str:
        payload = self.scene_pipeline.review_scene_images(episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "scenes" / "scene-review.json"
        passed = sum(1 for item in payload.get("scenes", []) if item.get("decision") == "pass")
        self._log_run(payload["episode_id"], "REVIEW_SCENE_IMAGES", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} scene review 已生成。\n"
            f"review_file={output_path}\n"
            f"scenes={len(payload.get('scenes', []))}\n"
            f"ready_for_storyboard={passed}"
        )

    def run_approve_character_assets(self, book_id: str, episode: str) -> str:
        payload = self.character_pipeline.approve_character_assets(book_id, episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-anchor-pack.json"
        self._log_run(payload["episode_id"], "APPROVE_CHARACTER_ASSETS", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} character assets 已入库。\n"
            f"anchor_pack={output_path}\n"
            f"characters={len(payload.get('characters', []))}"
        )

    def run_approve_scene_assets(self, episode: str) -> str:
        payload = self.scene_pipeline.approve_scene_assets(episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "scenes" / "scene-asset-pack.json"
        self._log_run(payload["episode_id"], "APPROVE_SCENE_ASSETS", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} scene assets 已入库。\n"
            f"scene_pack={output_path}\n"
            f"scenes={len(payload.get('scenes', []))}"
        )

    def run_export_character_reference_pack(self, book_id: str, episode: str) -> str:
        payload = self.character_pipeline.export_character_reference_pack(book_id, episode)
        output_path = self.project_root / "outputs" / payload["episode_id"] / "characters" / "character-reference-pack.json"
        self._log_run(payload["episode_id"], "EXPORT_CHARACTER_REFERENCE_PACK", "SUCCESS", str(output_path))
        return (
            f"{payload['episode_id']} character reference pack 已导出。\n"
            f"reference_pack={output_path}\n"
            f"characters={len(payload.get('characters', []))}"
        )

    def _resolve_episode(self, episode: str | None) -> str:
        if episode:
            return sanitize_episode_id(episode)
        statuses = detect_all_statuses(self.config)
        target = pick_default_episode(statuses)
        if not target:
            raise RuntimeError("未检测到可处理的剧本文件。")
        return target

    def _revise_director(self, episode: str, feedback: str) -> str:
        path = self.config.paths.outputs / episode / "01-director-analysis.md"
        if not path.exists():
            raise RuntimeError(f"缺少导演分析文件：{path}")
        session = self.sessions.get_or_create(episode, "director")
        artifact = path.read_text(encoding="utf-8")
        revision_messages = build_revision_prompt("阶段一", artifact, [feedback])
        artifact = self._chat("director_generate", self._with_session_history(session, revision_messages))
        self.sessions.append_history(session, revision_messages + [{"role": "assistant", "content": artifact}])
        script_text = self._get_script_file(episode).read_text(encoding="utf-8")
        artifact, _ = self._review_and_revise(
            episode,
            stage_name="阶段一",
            stage_key="director",
            role="director",
            artifact=artifact,
            business_skill="script-analysis-review-skill",
            upstream_context=script_text,
            revision_model_key="director_generate",
            validator=validate_director_artifact,
        )
        path.write_text(artifact, encoding="utf-8")
        output_dir = self.config.paths.outputs / episode
        (output_dir / "validation").mkdir(parents=True, exist_ok=True)
        (output_dir / "01-director-analysis.json").write_text(
            self._dump_json(parse_director_markdown(episode, artifact)),
            encoding="utf-8",
        )
        (output_dir / "validation" / "director-validation.json").write_text(
            self._dump_json(build_director_validation(parse_director_markdown(episode, artifact))),
            encoding="utf-8",
        )
        return f"已修订导演分析：{path}"

    def _revise_art(self, episode: str, feedback: str) -> str:
        director_file = self.config.paths.outputs / episode / "01-director-analysis.md"
        if not director_file.exists():
            raise RuntimeError(f"缺少导演分析文件：{director_file}")
        character_path = self.config.paths.assets / "character-prompts.md"
        scene_path = self.config.paths.assets / "scene-prompts.md"
        if not has_episode_block(character_path, episode, "CHARACTER") or not has_episode_block(scene_path, episode, "SCENE"):
            raise RuntimeError("缺少当前集的服化道资产块，无法修订。")
        artifact = (
            read_episode_block(character_path, episode, "CHARACTER")
            + "\n\n"
            + read_episode_block(scene_path, episode, "SCENE")
        )
        session = self.sessions.get_or_create(episode, "art-designer")
        revision_messages = build_revision_prompt("阶段二", artifact, [feedback])
        artifact = self._chat("art_designer", self._with_session_history(session, revision_messages))
        self.sessions.append_history(session, revision_messages + [{"role": "assistant", "content": artifact}])
        artifact, _ = self._review_and_revise(
            episode,
            stage_name="阶段二",
            stage_key="design",
            role="art-designer",
            artifact=artifact,
            business_skill="art-direction-review-skill",
            upstream_context=director_file.read_text(encoding="utf-8"),
            revision_model_key="art_designer",
            validator=self._validate_art_design_artifact,
        )
        character_content, scene_content = split_art_design_artifact(artifact)
        upsert_episode_block(character_path, episode, "CHARACTER", character_content)
        upsert_episode_block(scene_path, episode, "SCENE", scene_content)
        sync_design_assets(self.project_root, episode, character_content, scene_content)
        validation_path = self.config.paths.outputs / episode / "validation" / "design-validation.json"
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(self._dump_json(build_design_validation(character_content, scene_content)), encoding="utf-8")
        return f"已修订服化道资产：{character_path}，{scene_path}"

    def _revise_storyboard(self, episode: str, feedback: str) -> str:
        path = self.config.paths.outputs / episode / "02-seedance-prompts.md"
        if not path.exists():
            raise RuntimeError(f"缺少分镜文件：{path}")
        session = self.sessions.get_or_create(episode, "storyboard-artist")
        artifact = path.read_text(encoding="utf-8")
        revision_messages = build_revision_prompt("阶段三", artifact, [feedback])
        artifact = self._chat("storyboard_artist", self._with_session_history(session, revision_messages))
        self.sessions.append_history(session, revision_messages + [{"role": "assistant", "content": artifact}])
        director_file = self.config.paths.outputs / episode / "01-director-analysis.md"
        artifact, _ = self._review_and_revise(
            episode,
            stage_name="阶段三",
            stage_key="prompt",
            role="storyboard-artist",
            artifact=artifact,
            business_skill="seedance-prompt-review-skill",
            upstream_context=director_file.read_text(encoding="utf-8"),
            revision_model_key="storyboard_artist",
            validator=validate_seedance_artifact,
        )
        path.write_text(artifact, encoding="utf-8")
        output_dir = self.config.paths.outputs / episode
        reference_map = load_reference_map(self.project_root, episode)
        (output_dir / "validation").mkdir(parents=True, exist_ok=True)
        (output_dir / "02-seedance-prompts.json").write_text(
            self._dump_json(parse_seedance_markdown(episode, artifact)),
            encoding="utf-8",
        )
        (output_dir / "validation" / "prompt-validation.json").write_text(
            self._dump_json(build_seedance_validation(parse_seedance_markdown(episode, artifact), reference_map)),
            encoding="utf-8",
        )
        return f"已修订分镜文件：{path}"

    def _get_script_file(self, episode: str) -> Path:
        scripts = find_script_files(self.config.paths.scripts)
        path = scripts.get(episode)
        if path is None:
            raise RuntimeError(f"未找到剧本文件：{episode}")
        return path

    def _review_and_revise(
        self,
        episode: str,
        stage_name: str,
        stage_key: str,
        role: str,
        artifact: str,
        business_skill: str,
        upstream_context: str,
        revision_model_key: str,
        validator,
    ) -> tuple[str, bool]:
        session = self.sessions.get_or_create(episode, role)
        for round_index in range(1, self.config.review_max_auto_fix_rounds + 1):
            validator(artifact)
            business = self._run_review(stage_name, business_skill, artifact, upstream_context, session)
            compliance = self._run_compliance(stage_name, artifact, session)
            save_review_round(self.config.paths.reports, episode, stage_key, round_index, "business", business)
            save_review_round(self.config.paths.reports, episode, stage_key, round_index, "compliance", compliance)
            summary_path = save_review_summary(
                self.config.paths.reports,
                episode,
                stage_key,
                round_index,
                business,
                compliance,
            )
            self._log_review(episode, stage_name, "business", business.result, round_index, len(business.issues))
            self._log_review(episode, stage_name, "compliance", compliance.result, round_index, len(compliance.issues))
            if can_auto_accept_review(business, compliance):
                save_stage_acceptance(
                    self.config.paths.reports,
                    episode,
                    stage_key,
                    status="accepted",
                    source="auto",
                    summary=load_review_summary(self.config.paths.reports, episode, stage_key),
                    notes=f"Auto accepted from {summary_path.name}.",
                )
                save_stage_assessment_report(self.config.paths.reports, episode, stage_key)
                return artifact, True

            issues = merge_issue_lists(business.issues, compliance.issues)
            if round_index == self.config.review_max_auto_fix_rounds:
                save_stage_acceptance(
                    self.config.paths.reports,
                    episode,
                    stage_key,
                    status="pending",
                    source="system",
                    summary=load_review_summary(self.config.paths.reports, episode, stage_key),
                    notes="Auto review did not converge within max rounds.",
                )
                save_stage_assessment_report(self.config.paths.reports, episode, stage_key)
                return artifact, False
            revision_messages = build_revision_prompt(stage_name, artifact, issues)
            artifact = self._chat(revision_model_key, revision_messages)
            self.sessions.append_history(session, revision_messages + [{"role": "assistant", "content": artifact}])
        save_stage_acceptance(
            self.config.paths.reports,
            episode,
            stage_key,
            status="pending",
            source="system",
            summary=load_review_summary(self.config.paths.reports, episode, stage_key),
            notes="Reached unexpected fallback path.",
        )
        save_stage_assessment_report(self.config.paths.reports, episode, stage_key)
        return artifact, False

    def _run_review(self, stage_name: str, skill_key: str, artifact: str, upstream_context: str, session) -> ReviewOutcome:
        response = self._chat(
            "director_review",
            build_review_prompt(self._get_prompts(), stage_name, skill_key, artifact, upstream_context),
        )
        payload = extract_json_object(response)
        return parse_business_review_payload(payload)

    def _run_compliance(self, stage_name: str, artifact: str, session) -> ReviewOutcome:
        response = self._chat(
            "compliance_review",
            build_compliance_prompt(self._get_prompts(), stage_name, artifact),
        )
        payload = extract_json_object(response)
        return parse_compliance_review_payload(payload)

    def _log_run(self, episode: str, stage: str, status: str, output_file: str) -> None:
        append_jsonl(
            self.config.paths.logs / "run-log.jsonl",
            {
                "episode": episode,
                "stage": stage,
                "status": status,
                "output_file": output_file,
            },
        )

    def _log_review(self, episode: str, stage: str, review_type: str, result: str, round_index: int, issues_count: int) -> None:
        append_jsonl(
            self.config.paths.logs / "review-log.jsonl",
            {
                "episode": episode,
                "stage": stage,
                "review_type": review_type,
                "result": result,
                "round": round_index,
                "issues_count": issues_count,
            },
        )

    def _chat(self, model_key: str, messages: list[dict[str, str]]) -> str:
        model = self.config.models[model_key]
        api_settings = self.config.api_settings_for_model(model_key)
        last_error: Exception | None = None
        for _ in range(api_settings.max_retries):
            try:
                return self.llm.chat(model, messages)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        raise RuntimeError(f"模型调用失败，model_key={model_key}") from last_error

    def _validate_art_design_artifact(self, artifact: str) -> None:
        character_content, scene_content = split_art_design_artifact(artifact)
        validate_character_asset(character_content)
        validate_scene_asset(scene_content)

    def _stage_result_message(self, episode: str, stage_key: str, output_path: Path, accepted: bool) -> str:
        if accepted:
            return (
                f"{episode} {stage_key} 已自动通过审核并完成：{output_path}\n"
                f"assessment_report={self.config.paths.reports / 'assessments' / episode / f'{stage_key}.md'}"
            )
        summary = load_review_summary(self.config.paths.reports, episode, stage_key)
        recommendation = summary.get("recommendation", "manual_review_required")
        return (
            f"{episode} {stage_key} 已生成最新版本，但自动审核未收敛，已保存待人工放行版本：{output_path}\n"
            f"recommendation={recommendation}\n"
            f"assessment_report={self.config.paths.reports / 'assessments' / episode / f'{stage_key}.md'}\n"
            f"请先执行 review {episode} {stage_key}，再决定是否 accept {episode} {stage_key}"
        )

    def _format_accept_message(self, episode: str, stage: str, summary: dict, assessment_path: Path) -> str:
        business = summary.get("business", {})
        compliance = summary.get("compliance", {})
        return (
            f"{episode} {stage} 已人工放行。\n"
            f"business_result={business.get('result', 'UNKNOWN')}, "
            f"business_score={business.get('average_score', 'n/a')}, "
            f"compliance_result={compliance.get('result', 'UNKNOWN')}, "
            f"recommendation={summary.get('recommendation', 'n/a')}\n"
            f"review_summary={self.config.paths.reports / 'reviews' / episode / stage / 'summary.json'}\n"
            f"assessment_report={assessment_path}"
        )

    def _format_review_message(self, episode: str, stage: str, snapshot: dict, report_path: Path) -> str:
        return (
            f"{episode} {stage} 审核报告已生成。\n"
            f"business_result={snapshot['business_result']}, "
            f"business_score={snapshot['business_score']}, "
            f"quality_band={snapshot['quality_band']}, "
            f"compliance_result={snapshot['compliance_result']}, "
            f"recommendation={snapshot['recommendation']}\n"
            f"assessment_report={report_path}"
        )

    def _resolve_review_stages(self, stage: str) -> list[str]:
        if stage == "all":
            return ["director", "design", "prompt"]
        if stage not in {"director", "design", "prompt"}:
            raise RuntimeError(f"不支持的阶段: {stage}")
        return [stage]

    def _dump_json(self, payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _with_session_history(self, session, messages: list[dict[str, str]], limit: int = 6) -> list[dict[str, str]]:
        history = [item for item in self.sessions.load_history(session) if item.get("role") != "system"]
        current_system = [item for item in messages if item.get("role") == "system"]
        current_non_system = [item for item in messages if item.get("role") != "system"]
        if not history:
            return messages
        return current_system + history[-limit:] + current_non_system

    def _get_prompts(self):
        if self.prompts is None:
            self.prompts = PromptLoader(self.project_root).load()
        return self.prompts
