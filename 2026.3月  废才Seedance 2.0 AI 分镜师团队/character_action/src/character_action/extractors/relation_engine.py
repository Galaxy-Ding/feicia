from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..ids import build_relation_id
from ..models import CharacterRecord, NormalizedTextUnit, RelationRecord


@dataclass(slots=True)
class RelationBuildResult:
    relations: list[RelationRecord]


class RelationEngine:
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

    def build(
        self,
        book_id: str,
        language: str,
        characters: list[CharacterRecord],
        normalized_units: Iterable[NormalizedTextUnit],
    ) -> RelationBuildResult:
        alias_map = self._build_alias_map(characters, language)
        character_index = {item.character_id: item for item in characters}
        relation_buckets: dict[tuple[str, str], dict[str, object]] = {}
        for unit in normalized_units:
            evidence_by_mention_id = {item.linked_object_id: item.evidence_id for item in unit.evidences}
            for sentence, sent_start, sent_end in self._sentence_spans(unit.chunk.text, unit.sentences):
                sentence_mentions = [
                    mention
                    for mention in sorted(unit.mentions, key=lambda item: (item.span_start, item.span_end, item.mention_id))
                    if sent_start <= mention.span_start < mention.span_end <= sent_end
                ]
                if len(sentence_mentions) < 2:
                    continue
                seen_pairs: set[tuple[str, str]] = set()
                for left, right in zip(sentence_mentions, sentence_mentions[1:]):
                    left_id = self._resolve_character_id(alias_map, left.surface_form, left.normalized_form, language)
                    right_id = self._resolve_character_id(alias_map, right.surface_form, right.normalized_form, language)
                    if not left_id or not right_id or left_id == right_id:
                        continue
                    pair = tuple(sorted((left_id, right_id)))
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    context_start = max(sent_start, left.span_start - 16)
                    context_end = min(sent_end, right.span_end + 16)
                    local_context = unit.chunk.text[context_start:context_end]
                    relation_type = self._classify_relation_type(local_context or sentence, language)
                    bucket = relation_buckets.setdefault(
                        pair,
                        {
                            "relation_votes": {},
                            "evidence_ids": set(),
                            "occurrences": set(),
                        },
                    )
                    weight = 2 if relation_type != "interaction" else 1
                    votes = bucket["relation_votes"]
                    votes[relation_type] = votes.get(relation_type, 0) + weight
                    left_evidence = evidence_by_mention_id.get(left.mention_id)
                    right_evidence = evidence_by_mention_id.get(right.mention_id)
                    if left_evidence:
                        bucket["evidence_ids"].add(left_evidence)
                    if right_evidence:
                        bucket["evidence_ids"].add(right_evidence)
                    bucket["occurrences"].add((unit.chunk.chunk_id, sent_start, sent_end))

        relations: list[RelationRecord] = []
        for index, (pair, bucket) in enumerate(sorted(relation_buckets.items()), start=1):
            source_id, target_id = pair
            relation_type = self._select_relation_type(bucket["relation_votes"])
            confidence = self._compute_confidence(
                relation_type=relation_type,
                occurrence_count=len(bucket["occurrences"]),
                evidence_count=len(bucket["evidence_ids"]),
                source_character=character_index[source_id],
                target_character=character_index[target_id],
            )
            relations.append(
                RelationRecord(
                    relation_id=build_relation_id(index),
                    book_id=book_id,
                    source_character_id=source_id,
                    target_character_id=target_id,
                    relation_type=relation_type,
                    direction="bidirectional",
                    confidence=confidence,
                    evidence_ids=sorted(bucket["evidence_ids"]),
                    occurrence_count=len(bucket["occurrences"]),
                    review_status="pending" if confidence < 0.65 else "auto_approved",
                )
            )
        return RelationBuildResult(relations=relations)

    def _build_alias_map(self, characters: list[CharacterRecord], language: str) -> dict[str, str]:
        alias_candidates: dict[str, set[str]] = {}
        for character in characters:
            if self._looks_like_pronoun(character.canonical_name, language):
                continue
            names = [character.canonical_name, *character.aliases]
            for name in names:
                key = self._normalize_name(name, language)
                if not key or self._looks_like_pronoun(key, language):
                    continue
                alias_candidates.setdefault(key, set()).add(character.character_id)
        return {
            alias: next(iter(character_ids))
            for alias, character_ids in alias_candidates.items()
            if len(character_ids) == 1
        }

    def _resolve_character_id(self, alias_map: dict[str, str], surface_form: str, normalized_form: str, language: str) -> str:
        for candidate in (surface_form, normalized_form):
            key = self._normalize_name(candidate, language)
            if key in alias_map:
                return alias_map[key]
        return ""

    def _sentence_spans(self, text: str, sentences: list[str]) -> list[tuple[str, int, int]]:
        spans: list[tuple[str, int, int]] = []
        cursor = 0
        for sentence in sentences:
            fragment = sentence.strip()
            if not fragment:
                continue
            start = text.find(fragment, cursor)
            if start < 0:
                start = text.find(fragment)
            if start < 0:
                continue
            end = start + len(fragment)
            spans.append((fragment, start, end))
            cursor = end
        if spans:
            return spans
        return [(text, 0, len(text))]

    def _classify_relation_type(self, sentence: str, language: str) -> str:
        text = sentence.lower() if language == "en" else sentence
        patterns = (
            ("romantic", ("love", "kiss", "marry", "lover", "爱", "喜欢", "恋", "吻")),
            ("hostile", ("enemy", "hate", "fight", "attack", "kill", "敌", "仇", "战", "杀")),
            ("family", ("mother", "father", "brother", "sister", "wife", "husband", "母", "父", "兄", "弟", "姐", "妹", "妻", "夫")),
            ("mentor", ("mentor", "master", "teacher", "师父", "师傅", "老师")),
            ("superior_subordinate", ("captain", "commander", "leader", "boss", "lord", "sir", "队长", "统领", "首领", "大人")),
            ("dialogue", ("said", "asked", "replied", "warned", "told", "reminded", "提醒", "说道", "说", "问", "答", "夜谈", "交谈")),
            ("interaction", ("met", "greeted", "studied", "with", "together", "与", "和", "一起", "看着")),
        )
        for relation_type, markers in patterns:
            if any(marker in text for marker in markers):
                return relation_type
        return "interaction"

    def _select_relation_type(self, votes: dict[str, int]) -> str:
        return max(sorted(votes.items()), key=lambda item: (item[1], item[0]))[0]

    def _compute_confidence(
        self,
        *,
        relation_type: str,
        occurrence_count: int,
        evidence_count: int,
        source_character: CharacterRecord,
        target_character: CharacterRecord,
    ) -> float:
        confidence = 0.34
        confidence += 0.12 * min(occurrence_count, 3)
        confidence += 0.05 * min(evidence_count, 4)
        if relation_type != "interaction":
            confidence += 0.08
        if source_character.review_status == "auto_approved" and target_character.review_status == "auto_approved":
            confidence += 0.05
        return round(min(confidence, 0.95), 2)

    def _normalize_name(self, name: str, language: str) -> str:
        normalized = " ".join(name.strip().split())
        if not normalized:
            return ""
        return normalized.lower() if language == "en" else normalized

    def _looks_like_pronoun(self, name: str, language: str) -> bool:
        normalized = self._normalize_name(name, language)
        if not normalized:
            return True
        if language == "en":
            return normalized in self._EN_PRONOUNS
        return normalized in self._ZH_PRONOUNS
