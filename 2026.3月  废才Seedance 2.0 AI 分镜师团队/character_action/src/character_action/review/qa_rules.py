from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import re

from ..ids import build_qa_finding_id, build_review_task_id
from ..models import CharacterRecord, QAFindingRecord, RelationRecord, ReviewTaskRecord


@dataclass(slots=True)
class QARunResult:
    findings: list[QAFindingRecord]
    review_tasks: list[ReviewTaskRecord]


class QARuleEngine:
    _TOKEN_RE = re.compile(r"[a-z]+")
    _EN_PRONOUNS = {
        "he",
        "him",
        "his",
        "she",
        "her",
        "hers",
        "they",
        "them",
        "their",
        "theirs",
        "we",
        "us",
        "our",
        "ours",
        "i",
        "me",
        "my",
        "mine",
        "you",
        "your",
        "yours",
    }
    _ZH_PRONOUNS = {"他", "她", "它", "他们", "她们", "它们", "自己"}
    _CONTEXT_RELATION_TYPES = {"dialogue", "interaction"}
    _RELATION_TYPE_COMPATIBILITY = {
        frozenset({"family", "romantic"}),
        frozenset({"mentor", "superior_subordinate"}),
    }
    _EN_GENDER_MARKERS = {
        "male": {
            "boy",
            "brother",
            "father",
            "gentleman",
            "husband",
            "king",
            "lord",
            "man",
            "mister",
            "mr",
            "prince",
            "sir",
            "son",
            "uncle",
        },
        "female": {
            "aunt",
            "daughter",
            "girl",
            "lady",
            "madam",
            "miss",
            "mother",
            "mrs",
            "ms",
            "princess",
            "queen",
            "sister",
            "wife",
            "woman",
        },
    }
    _ZH_GENDER_MARKERS = {
        "male": {"父亲", "哥哥", "弟弟", "公子", "少爷", "先生", "叔叔", "丈夫", "王子", "皇子"},
        "female": {"公主", "太太", "夫人", "妻子", "姐姐", "妹妹", "女士", "小姐", "母亲", "阿姨"},
    }

    def run(
        self,
        *,
        run_id: str,
        book_id: str,
        language: str,
        characters: list[CharacterRecord],
        relations: list[RelationRecord],
    ) -> QARunResult:
        findings: list[QAFindingRecord] = []
        review_tasks: list[ReviewTaskRecord] = []
        character_index = {character.character_id: character for character in characters}
        finding_index = 1
        task_index = 1

        def append_finding(
            *,
            finding_type: str,
            severity: str,
            target_type: str,
            target_id: str,
            reason_codes: list[str],
            message: str,
            evidence_ids: list[str],
            task_type: str | None = None,
            review_patch: dict[str, object] | None = None,
        ) -> None:
            nonlocal finding_index, task_index
            findings.append(
                QAFindingRecord(
                    finding_id=build_qa_finding_id(finding_index),
                    run_id=run_id,
                    book_id=book_id,
                    finding_type=finding_type,
                    severity=severity,
                    target_type=target_type,
                    target_id=target_id,
                    reason_codes=list(reason_codes),
                    message=message,
                    evidence_ids=list(evidence_ids),
                    status="open",
                )
            )
            finding_index += 1
            if task_type:
                review_tasks.append(
                    ReviewTaskRecord(
                        task_id=build_review_task_id(task_index),
                        run_id=run_id,
                        task_type=task_type,
                        target_id=target_id,
                        reason_codes=list(reason_codes),
                        status="open",
                        review_patch=dict(review_patch or {}),
                    )
                )
                task_index += 1

        for character in characters:
            if self._looks_like_pronoun(character.canonical_name, language):
                append_finding(
                    finding_type="invalid_character_name",
                    severity="high",
                    target_type="character",
                    target_id=character.character_id,
                    reason_codes=["PRONOUN_CANONICAL_NAME"],
                    message=f"Character {character.character_id} uses pronoun-like canonical_name {character.canonical_name!r}.",
                    evidence_ids=character.evidence_ids[:3],
                    task_type="invalid_character_name",
                    review_patch={"canonical_name": character.canonical_name, "action": "rename_or_merge"},
                )
            if len(character.evidence_ids) < 2:
                append_finding(
                    finding_type="character_evidence_gap",
                    severity="medium",
                    target_type="character",
                    target_id=character.character_id,
                    reason_codes=["LOW_EVIDENCE_CHARACTER"],
                    message=f"Character {character.character_id} has only {len(character.evidence_ids)} evidence item(s).",
                    evidence_ids=character.evidence_ids[:3],
                    task_type="character_evidence_gap",
                    review_patch={"minimum_evidence": 2},
                )
            conflicting_gender_markers = self._collect_conflicting_gender_markers(character, language)
            if conflicting_gender_markers:
                append_finding(
                    finding_type="character_attribute_conflict",
                    severity="medium",
                    target_type="character",
                    target_id=character.character_id,
                    reason_codes=["CONFLICTING_GENDER_MARKERS"],
                    message=(
                        f"Character {character.character_id} has conflicting gender markers in names or roles: "
                        f"{self._format_conflicting_markers(conflicting_gender_markers)}."
                    ),
                    evidence_ids=character.evidence_ids[:3],
                    task_type="character_attribute_conflict",
                    review_patch={
                        "attribute": "gender",
                        "markers": {key: sorted(value) for key, value in conflicting_gender_markers.items()},
                    },
                )

        alias_index: dict[str, list[CharacterRecord]] = {}
        for character in characters:
            for raw_name in [character.canonical_name, *character.aliases]:
                alias = self._normalize_alias(raw_name, language)
                if alias:
                    alias_index.setdefault(alias, []).append(character)
        for alias, matched_characters in sorted(alias_index.items()):
            character_ids = sorted({item.character_id for item in matched_characters})
            canonical_names = sorted({item.canonical_name for item in matched_characters})
            if len(character_ids) < 2:
                continue
            append_finding(
                finding_type="alias_conflict",
                severity="medium",
                target_type="alias",
                target_id=alias,
                reason_codes=["ALIAS_CONFLICT"],
                message=f"Alias {alias!r} maps to multiple characters: {', '.join(canonical_names)}.",
                evidence_ids=[],
                task_type="alias_conflict_review",
                review_patch={"character_ids": character_ids, "canonical_names": canonical_names},
            )

        seen_pairs: dict[tuple[str, str], list[RelationRecord]] = {}
        for relation in relations:
            if relation.confidence < 0.7:
                append_finding(
                    finding_type="low_confidence_relation",
                    severity="medium",
                    target_type="relation",
                    target_id=relation.relation_id,
                    reason_codes=["LOW_CONFIDENCE_RELATION"],
                    message=f"Relation {relation.relation_id} confidence is {relation.confidence:.2f}.",
                    evidence_ids=relation.evidence_ids[:4],
                    task_type="low_confidence_relation",
                    review_patch={"confidence": relation.confidence, "relation_type": relation.relation_type},
                )
            if len(relation.evidence_ids) < 2:
                append_finding(
                    finding_type="relation_evidence_gap",
                    severity="medium",
                    target_type="relation",
                    target_id=relation.relation_id,
                    reason_codes=["LOW_EVIDENCE_RELATION"],
                    message=f"Relation {relation.relation_id} has only {len(relation.evidence_ids)} evidence item(s).",
                    evidence_ids=relation.evidence_ids[:4],
                    task_type="relation_evidence_gap",
                    review_patch={"minimum_evidence": 2, "relation_type": relation.relation_type},
                )
            pair = tuple(sorted((relation.source_character_id, relation.target_character_id)))
            seen_pairs.setdefault(pair, []).append(relation)
        for pair, matched_relations in sorted(seen_pairs.items()):
            relation_types = {relation.relation_type for relation in matched_relations}
            conflicting_types = self._find_conflicting_relation_types(relation_types)
            if len(conflicting_types) < 2:
                continue
            pair_id = f"{pair[0]}::{pair[1]}"
            relation_ids = sorted(relation.relation_id for relation in matched_relations)
            evidence_ids = sorted({evidence_id for relation in matched_relations for evidence_id in relation.evidence_ids})[:6]
            pair_label = self._format_relation_pair_label(pair, character_index)
            append_finding(
                finding_type="relation_type_conflict",
                severity="high",
                target_type="relation_pair",
                target_id=pair_id,
                reason_codes=["RELATION_TYPE_CONFLICT"],
                message=f"Relation pair {pair_label} has conflicting relation types: {', '.join(conflicting_types)}.",
                evidence_ids=evidence_ids,
                task_type="relation_type_conflict",
                review_patch={"relation_types": conflicting_types, "relation_ids": relation_ids},
            )
        return QARunResult(findings=findings, review_tasks=review_tasks)

    def _looks_like_pronoun(self, value: str, language: str) -> bool:
        normalized = self._normalize_alias(value, language)
        if not normalized:
            return True
        if language == "en":
            return normalized in self._EN_PRONOUNS
        return normalized in self._ZH_PRONOUNS

    def _normalize_alias(self, value: str, language: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            return ""
        return normalized.lower() if language == "en" else normalized

    def _find_conflicting_relation_types(self, relation_types: set[str]) -> list[str]:
        semantic_types = sorted(relation_type for relation_type in relation_types if relation_type not in self._CONTEXT_RELATION_TYPES)
        if len(semantic_types) < 2:
            return []
        conflicting_types: set[str] = set()
        for left, right in combinations(semantic_types, 2):
            if frozenset({left, right}) in self._RELATION_TYPE_COMPATIBILITY:
                continue
            conflicting_types.update({left, right})
        return sorted(conflicting_types)

    def _collect_conflicting_gender_markers(self, character: CharacterRecord, language: str) -> dict[str, set[str]]:
        markers = {"male": set(), "female": set()}
        for value in [character.canonical_name, *character.aliases, *character.roles]:
            if not value.strip():
                continue
            for gender, matched_markers in self._extract_gender_markers(value, language).items():
                markers[gender].update(matched_markers)
        return {gender: values for gender, values in markers.items() if values} if all(markers.values()) else {}

    def _extract_gender_markers(self, value: str, language: str) -> dict[str, set[str]]:
        normalized = self._normalize_alias(value, language)
        if not normalized:
            return {"male": set(), "female": set()}
        marker_map = self._EN_GENDER_MARKERS if language == "en" else self._ZH_GENDER_MARKERS
        if language == "en":
            tokens = set(self._TOKEN_RE.findall(normalized))
            return {
                gender: {marker for marker in markers if marker in tokens}
                for gender, markers in marker_map.items()
            }
        return {
            gender: {marker for marker in markers if marker in normalized}
            for gender, markers in marker_map.items()
        }

    def _format_conflicting_markers(self, markers: dict[str, set[str]]) -> str:
        return "; ".join(f"{gender}={', '.join(sorted(values))}" for gender, values in sorted(markers.items()))

    def _format_relation_pair_label(
        self,
        pair: tuple[str, str],
        character_index: dict[str, CharacterRecord],
    ) -> str:
        left = character_index.get(pair[0])
        right = character_index.get(pair[1])
        if left and right:
            return f"{left.canonical_name} <-> {right.canonical_name} ({pair[0]}::{pair[1]})"
        return f"{pair[0]}::{pair[1]}"
