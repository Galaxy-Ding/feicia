from __future__ import annotations

import json
from dataclasses import dataclass

from ..ids import build_character_id
from ..llm_client import LLMModelSettings
from ..models import CharacterRecord, NormalizedTextUnit


@dataclass(slots=True)
class LLMCharacterExtractionResult:
    chunk_candidates: list[dict[str, object]]
    reviewer_payload: dict[str, object]
    characters: list[CharacterRecord]
    ambiguous_aliases: list[dict[str, object]]


class DualLLMCharacterExtractor:
    def __init__(
        self,
        llm_client,
        *,
        extractor_model: LLMModelSettings,
        reviewer_model: LLMModelSettings,
    ) -> None:
        self.llm = llm_client
        self.extractor_model = extractor_model
        self.reviewer_model = reviewer_model

    def extract(self, *, book_id: str, language: str, units: list[NormalizedTextUnit]) -> LLMCharacterExtractionResult:
        chunk_candidates: list[dict[str, object]] = []
        for unit in units:
            messages = [
                {"role": "system", "content": self._extractor_system_prompt(language)},
                {"role": "user", "content": self._extractor_user_prompt(unit)},
            ]
            raw = self.llm.chat(self.extractor_model, messages)
            payload = self._parse_json_document(raw)
            chunk_candidates.append(
                {
                    "chunk_id": unit.chunk.chunk_id,
                    "chapter_id": unit.chapter_id,
                    "text": unit.chunk.text,
                    "candidates": list(payload.get("characters", [])),
                }
            )

        review_messages = [
            {"role": "system", "content": self._reviewer_system_prompt(language)},
            {"role": "user", "content": self._reviewer_user_prompt(book_id, chunk_candidates)},
        ]
        reviewer_payload = self._parse_json_document(self.llm.chat(self.reviewer_model, review_messages))
        characters = self._build_character_records(
            book_id=book_id,
            language=language,
            units=units,
            payload=list(reviewer_payload.get("characters", [])),
        )
        ambiguous_aliases = self._build_ambiguous_aliases(characters, language)
        return LLMCharacterExtractionResult(
            chunk_candidates=chunk_candidates,
            reviewer_payload=reviewer_payload,
            characters=characters,
            ambiguous_aliases=ambiguous_aliases,
        )

    def _build_character_records(
        self,
        *,
        book_id: str,
        language: str,
        units: list[NormalizedTextUnit],
        payload: list[object],
    ) -> list[CharacterRecord]:
        evidence_lookup = self._build_evidence_lookup(units, language)
        merged: dict[str, dict[str, object]] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            canonical_name = str(item.get("canonical_name", "")).strip()
            if not canonical_name:
                continue
            bucket = merged.setdefault(
                canonical_name,
                {
                    "aliases": set(),
                    "roles": set(),
                    "evidence_ids": set(),
                    "summary": "",
                    "confidence": 0.0,
                },
            )
            aliases = {str(alias).strip() for alias in item.get("aliases", []) if str(alias).strip()}
            bucket["aliases"].update(alias for alias in aliases if alias != canonical_name)
            roles = {str(role).strip() for role in item.get("roles", []) if str(role).strip()}
            bucket["roles"].update(roles or {"person"})
            summary = str(item.get("summary", "")).strip()
            if summary and not bucket["summary"]:
                bucket["summary"] = summary
            bucket["confidence"] = max(bucket["confidence"], float(item.get("confidence", 0.75) or 0.75))

            evidence_surfaces = {canonical_name, *bucket["aliases"], *aliases}
            for surface in item.get("evidence_surfaces", []):
                normalized = str(surface).strip()
                if normalized:
                    evidence_surfaces.add(normalized)
            for surface in evidence_surfaces:
                bucket["evidence_ids"].update(evidence_lookup.get(self._normalize(surface, language), []))

        records: list[CharacterRecord] = []
        for index, canonical_name in enumerate(sorted(merged), start=1):
            item = merged[canonical_name]
            confidence = round(min(max(float(item["confidence"]), 0.0), 0.99), 2)
            evidence_ids = sorted(item["evidence_ids"])[:5]
            records.append(
                CharacterRecord(
                    character_id=build_character_id(index),
                    book_id=book_id,
                    canonical_name=canonical_name,
                    aliases=sorted(item["aliases"]),
                    roles=sorted(item["roles"]) if item["roles"] else ["person"],
                    summary=str(item["summary"] or "LLM extracted character cluster."),
                    confidence=confidence,
                    evidence_ids=evidence_ids,
                    mention_count=max(1, len(evidence_ids)),
                    review_status="pending" if confidence < 0.6 else "auto_approved",
                )
            )
        return records

    def _build_evidence_lookup(self, units: list[NormalizedTextUnit], language: str) -> dict[str, list[str]]:
        lookup: dict[str, list[str]] = {}
        for unit in units:
            for mention, evidence in zip(unit.mentions, unit.evidences):
                for value in {mention.surface_form, mention.normalized_form}:
                    normalized = self._normalize(value, language)
                    if normalized:
                        lookup.setdefault(normalized, []).append(evidence.evidence_id)
        return lookup

    def _build_ambiguous_aliases(self, characters: list[CharacterRecord], language: str) -> list[dict[str, object]]:
        alias_map: dict[str, set[str]] = {}
        for character in characters:
            for value in [character.canonical_name, *character.aliases]:
                normalized = self._normalize(value, language)
                if not normalized:
                    continue
                alias_map.setdefault(normalized, set()).add(character.canonical_name)
        return [
            {"alias": alias, "canonical_candidates": sorted(candidates)}
            for alias, candidates in sorted(alias_map.items())
            if len(candidates) > 1
        ]

    def _extractor_system_prompt(self, language: str) -> str:
        return (
            f"你是{language}小说人物候选抽取器。"
            "只返回严格 JSON，不要写解释。"
            "目标是从单个文本块中提取人物候选，包括本名、简称、称谓、官职、自称、关系称谓。"
            "输出格式："
            '{"characters":[{"canonical_name":"","aliases":[],"roles":[],"evidence_surfaces":[],"confidence":0.0}]}'
        )

    def _extractor_user_prompt(self, unit: NormalizedTextUnit) -> str:
        return json.dumps(
            {
                "chunk_id": unit.chunk.chunk_id,
                "chapter_id": unit.chapter_id,
                "text": unit.chunk.text,
                "existing_mentions": [item.surface_form for item in unit.mentions],
            },
            ensure_ascii=False,
            indent=2,
        )

    def _reviewer_system_prompt(self, language: str) -> str:
        return (
            f"你是{language}小说人物归并复核器。"
            "你会收到多个 chunk 的人物候选，请做全书级去重、别名归并和保守复核。"
            "一个 character 只能对应一个人物簇。无法安全合并的称谓请单独保留并降低 confidence。"
            "只返回严格 JSON，不要写解释。"
            "输出格式："
            '{"characters":[{"canonical_name":"","aliases":[],"roles":[],"evidence_surfaces":[],"summary":"","confidence":0.0}]}'
        )

    def _reviewer_user_prompt(self, book_id: str, chunk_candidates: list[dict[str, object]]) -> str:
        return json.dumps(
            {
                "book_id": book_id,
                "chunks": chunk_candidates,
            },
            ensure_ascii=False,
            indent=2,
        )

    def _parse_json_document(self, raw: str) -> dict[str, object]:
        text = raw.strip()
        if text.startswith("```"):
            parts = [part.strip() for part in text.split("```") if part.strip()]
            for part in parts:
                cleaned = part[4:].strip() if part.startswith("json") else part
                try:
                    payload = json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    return payload
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start < 0 or end < start:
                raise RuntimeError("Model output is not valid JSON")
            payload = json.loads(text[start : end + 1])
        if not isinstance(payload, dict):
            raise RuntimeError("Model output must be a JSON object")
        return payload

    def _normalize(self, value: str, language: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            return ""
        return normalized.lower() if language == "en" else normalized
