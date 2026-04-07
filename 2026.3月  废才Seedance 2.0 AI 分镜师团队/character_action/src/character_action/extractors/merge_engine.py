from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from ..ids import build_character_id
from ..models import CharacterRecord, NormalizedTextUnit


@dataclass(slots=True)
class AliasMergeResult:
    characters: list[CharacterRecord]
    ambiguous_aliases: list[dict[str, object]]


class AliasMergeEngine:
    _EN_TOKEN_RE = re.compile(r"[a-z]+")
    _EN_ROLE_MARKERS = (
        ("captain", {"captain"}),
        ("leader", {"commander", "general", "leader", "boss", "chief"}),
        ("royalty", {"king", "queen", "prince", "princess", "emperor", "empress"}),
        ("guard", {"guard", "watchman", "sentinel", "gatekeeper"}),
        ("attendant", {"attendant", "servant", "maid", "butler", "steward", "retainer"}),
        ("mentor", {"mentor", "master", "teacher", "tutor", "professor"}),
        ("healer", {"doctor", "healer", "physician", "surgeon"}),
        ("clergy", {"priest", "monk", "nun"}),
    )
    _ZH_ROLE_MARKERS = (
        ("captain", {"队长", "船长"}),
        ("leader", {"统领", "将军", "司令", "首领", "头领"}),
        ("royalty", {"皇帝", "皇后", "太子", "公主", "王爷", "郡主"}),
        ("guard", {"守门", "侍卫", "护卫", "门房", "禁军"}),
        ("attendant", {"内侍", "侍女", "女官", "仆人", "丫鬟", "管家"}),
        ("mentor", {"师父", "师傅", "老师", "教习"}),
        ("healer", {"医师", "大夫", "郎中"}),
        ("clergy", {"方丈", "住持", "僧人", "道长"}),
    )

    def merge(self, book_id: str, language: str, normalized_units: Iterable[NormalizedTextUnit]) -> AliasMergeResult:
        mention_groups: dict[str, dict[str, object]] = {}
        alias_to_canonical: dict[str, set[str]] = {}
        for unit in normalized_units:
            for mention, evidence in zip(unit.mentions, unit.evidences):
                canonical_key = self._canonical_key(mention.surface_form, language)
                if not canonical_key:
                    continue
                bucket = mention_groups.setdefault(
                    canonical_key,
                    {
                        "display_names": {},
                        "aliases": set(),
                        "evidence_ids": [],
                        "mention_count": 0,
                    },
                )
                bucket["display_names"][mention.surface_form] = bucket["display_names"].get(mention.surface_form, 0) + 1
                bucket["evidence_ids"].append(evidence.evidence_id)
                bucket["mention_count"] += 1
                for alias in self._possible_aliases(mention.surface_form, language):
                    alias_to_canonical.setdefault(alias, set()).add(canonical_key)
                    bucket["aliases"].add(alias)

        ambiguous_aliases = [
            {"alias": alias, "canonical_candidates": sorted(options)}
            for alias, options in alias_to_canonical.items()
            if len(options) > 1
        ]
        characters: list[CharacterRecord] = []
        for index, (canonical_key, bucket) in enumerate(sorted(mention_groups.items()), start=1):
            display_names = bucket["display_names"]
            canonical_name = max(display_names.items(), key=lambda item: (item[1], len(item[0]), item[0]))[0]
            aliases = sorted(
                alias
                for alias in bucket["aliases"]
                if alias != canonical_name and alias not in {canonical_key, canonical_name.lower()}
            )
            roles = self._infer_roles(
                language=language,
                names=[canonical_name, *aliases, *display_names.keys()],
            )
            confidence = min(0.98, 0.45 + 0.08 * min(bucket["mention_count"], 5) + 0.05 * min(len(aliases), 3))
            if any(canonical_key in item["canonical_candidates"] for item in ambiguous_aliases):
                confidence = min(confidence, 0.58)
            characters.append(
                CharacterRecord(
                    character_id=build_character_id(index),
                    book_id=book_id,
                    canonical_name=canonical_name,
                    aliases=aliases,
                    roles=roles,
                    summary=self._build_summary(int(bucket["mention_count"]), roles),
                    confidence=round(confidence, 2),
                    evidence_ids=list(bucket["evidence_ids"][:5]),
                    mention_count=int(bucket["mention_count"]),
                    review_status="pending" if confidence < 0.6 else "auto_approved",
                )
            )
        return AliasMergeResult(characters=characters, ambiguous_aliases=ambiguous_aliases)

    def _canonical_key(self, name: str, language: str) -> str:
        normalized = " ".join(name.strip().split())
        if not normalized:
            return ""
        return normalized.lower() if language == "en" else normalized

    def _possible_aliases(self, name: str, language: str) -> list[str]:
        normalized = " ".join(name.strip().split())
        if not normalized:
            return []
        aliases = {normalized}
        if language == "en":
            parts = normalized.split()
            if len(parts) > 1:
                aliases.add(parts[0])
                aliases.add(parts[-1])
        else:
            if len(normalized) >= 3:
                aliases.add(normalized[-2:])
                aliases.add(normalized[:1])
        return sorted(alias for alias in aliases if alias)

    def _infer_roles(self, *, language: str, names: list[str]) -> list[str]:
        role_markers = self._EN_ROLE_MARKERS if language == "en" else self._ZH_ROLE_MARKERS
        inferred_roles: list[str] = []
        seen_roles: set[str] = set()
        texts = [item for item in names if item.strip()]
        for role, markers in role_markers:
            if self._contains_role_marker(texts, markers, language):
                inferred_roles.append(role)
                seen_roles.add(role)
        if "person" not in seen_roles:
            inferred_roles.append("person")
        return inferred_roles

    def _contains_role_marker(self, texts: list[str], markers: set[str], language: str) -> bool:
        for text in texts:
            normalized = " ".join(text.strip().split())
            if not normalized:
                continue
            if language == "en":
                tokens = set(self._EN_TOKEN_RE.findall(normalized.lower()))
                if markers & tokens:
                    return True
                continue
            if any(marker in normalized for marker in markers):
                return True
        return False

    def _build_summary(self, mention_count: int, roles: list[str]) -> str:
        non_default_roles = [role for role in roles if role != "person"]
        if non_default_roles:
            return (
                f"Detected from {mention_count} mentions in normalized units. "
                f"Inferred roles: {', '.join(non_default_roles)}."
            )
        return f"Detected from {mention_count} mentions in normalized units."
