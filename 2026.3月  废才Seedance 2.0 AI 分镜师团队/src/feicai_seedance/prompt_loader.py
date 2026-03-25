from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PromptBundle:
    orchestrator: str
    agent_prompts: dict[str, str]
    skill_prompts: dict[str, str]
    template_prompts: dict[str, str]
    extra_prompts: dict[str, str]


class PromptLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self) -> PromptBundle:
        agents_root = self.root / "agents"
        skills_root = self.root / "skills"

        agent_prompts = {
            "director": (agents_root / "director.md").read_text(encoding="utf-8"),
            "art-designer": (agents_root / "art-designer.md").read_text(encoding="utf-8"),
            "storyboard-artist": (agents_root / "storyboard-artist.md").read_text(encoding="utf-8"),
        }

        skill_paths = {
            "director-skill": skills_root / "director-skill" / "SKILL.md",
            "art-design-skill": skills_root / "art-design-skill" / "SKILL.md",
            "seedance-storyboard-skill": skills_root / "seedance-storyboard-skill" / "SKILL.md",
            "script-analysis-review-skill": skills_root / "script-analysis-review-skill" / "SKILL.md",
            "art-direction-review-skill": skills_root / "art-direction-review-skill" / "SKILL.md",
            "seedance-prompt-review-skill": skills_root / "seedance-prompt-review-skill" / "SKILL.md",
            "compliance-review-skill": skills_root / "compliance-review-skill" / "SKILL.md",
            "gemini-image-prompt-guide": skills_root / "art-design-skill" / "gemini-image-prompt-guide.md",
            "seedance-prompt-methodology": skills_root / "seedance-storyboard-skill" / "seedance-prompt-methodology.md",
        }

        template_paths = {
            "director-analysis-template": skills_root / "director-skill" / "templates" / "director-analysis-template.md",
            "art-design-template": skills_root / "art-design-skill" / "templates" / "art-design-template.md",
            "seedance-prompts-template": skills_root / "seedance-storyboard-skill" / "templates" / "seedance-prompts-template.md",
        }

        extra_paths = {
            "character-examples": skills_root / "art-design-skill" / "examples" / "character-prompt-examples.md",
            "scene-examples": skills_root / "art-design-skill" / "examples" / "scene-prompt-examples.md",
            "seedance-examples": skills_root / "seedance-storyboard-skill" / "examples" / "seedance-prompt-examples.md",
        }

        return PromptBundle(
            orchestrator=(self.root / "CLAUDE.md").read_text(encoding="utf-8"),
            agent_prompts=agent_prompts,
            skill_prompts={key: path.read_text(encoding="utf-8") for key, path in skill_paths.items()},
            template_prompts={key: path.read_text(encoding="utf-8") for key, path in template_paths.items()},
            extra_prompts={key: path.read_text(encoding="utf-8") for key, path in extra_paths.items()},
        )
