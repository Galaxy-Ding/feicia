from __future__ import annotations

import unittest

from character_action.extractors import RelationEngine
from character_action.models import CharacterRecord, ChunkRecord, EvidenceRecord, MentionRecord, NormalizedTextUnit


def _character(character_id: str, name: str, *, aliases: list[str] | None = None, review_status: str = "auto_approved") -> CharacterRecord:
    return CharacterRecord(
        character_id=character_id,
        book_id="book_demo",
        canonical_name=name,
        aliases=aliases or [],
        roles=["person"],
        summary="demo",
        confidence=0.8,
        evidence_ids=[],
        mention_count=2,
        review_status=review_status,
    )


def _unit(chunk_id: str, language: str, text: str, mentions: list[tuple[str, int, int]]) -> NormalizedTextUnit:
    mention_rows = []
    evidence_rows = []
    for index, (name, start, end) in enumerate(mentions, start=1):
        mention_id = f"{chunk_id}_mn_{index:04d}"
        mention_rows.append(
            MentionRecord(
                mention_id=mention_id,
                chunk_id=chunk_id,
                surface_form=name,
                normalized_form=name.lower() if language == "en" else name,
                entity_type="person",
                speaker_hint="",
                span_start=start,
                span_end=end,
            )
        )
        evidence_rows.append(
            EvidenceRecord(
                evidence_id=f"{chunk_id}_ev_{index:04d}",
                book_id="book_demo",
                chapter_id="ch_0001",
                chunk_id=chunk_id,
                quote_text=text[max(0, start - 8) : min(len(text), end + 8)],
                span_start=start,
                span_end=end,
                linked_object_type="mention",
                linked_object_id=mention_id,
            )
        )
    return NormalizedTextUnit(
        book_id="book_demo",
        chapter_id="ch_0001",
        chunk=ChunkRecord(chunk_id=chunk_id, chapter_id="ch_0001", chunk_index=1, text=text, char_start=0, char_end=len(text)),
        language=language,
        sentences=[text],
        mentions=mention_rows,
        evidences=evidence_rows,
        adapter_name="test",
    )


class RelationEngineTest(unittest.TestCase):
    def test_relation_engine_builds_relations_for_three_cases(self) -> None:
        engine = RelationEngine()
        cases = [
            (
                "en",
                [_character("char_000001", "Alice Rowan", aliases=["Alice"]), _character("char_000002", "Marcus Vale", aliases=["Marcus"])],
                [
                    _unit(
                        "ch_0001_ck_0001",
                        "en",
                        "Marcus Vale greeted Alice Rowan and warned her to stay close.",
                        [("Marcus Vale", 0, 11), ("Alice Rowan", 20, 31), ("her", 43, 46)],
                    )
                ],
            ),
            (
                "zh",
                [_character("char_000001", "林晚"), _character("char_000002", "顾昭")],
                [_unit("ch_0001_ck_0001", "zh", "林晚与顾昭在灯下夜谈。", [("林晚", 0, 2), ("顾昭", 3, 5)])],
            ),
            (
                "en",
                [
                    _character("char_000001", "Captain Nora", aliases=["Nora"], review_status="pending"),
                    _character("char_000002", "Marcus Vale", aliases=["Marcus"]),
                    _character("char_000003", "she", review_status="pending"),
                ],
                [_unit("ch_0001_ck_0001", "en", "Captain Nora studied Marcus Vale before she answered.", [("Captain Nora", 0, 12), ("Marcus Vale", 21, 32), ("she", 40, 43)])],
            ),
        ]
        for language, characters, units in cases:
            result = engine.build("book_demo", language, characters, units)
            self.assertGreaterEqual(len(result.relations), 1)
            self.assertTrue(all(item.evidence_ids for item in result.relations))
            self.assertTrue(all(item.source_character_id != "char_000003" for item in result.relations))


if __name__ == "__main__":
    unittest.main()
