from __future__ import annotations

import random
import unittest

from character_action.extractors import AliasMergeEngine
from character_action.models import ChunkRecord, EvidenceRecord, MentionRecord, NormalizedTextUnit
from character_action.review import build_review_tasks


def _unit(chunk_id: str, language: str, names: list[str]) -> NormalizedTextUnit:
    mentions = []
    evidences = []
    cursor = 0
    for index, name in enumerate(names, start=1):
        mentions.append(
            MentionRecord(
                mention_id=f"{chunk_id}_mn_{index:04d}",
                chunk_id=chunk_id,
                surface_form=name,
                normalized_form=name.lower() if language == "en" else name,
                entity_type="person",
                speaker_hint="",
                span_start=cursor,
                span_end=cursor + len(name),
            )
        )
        evidences.append(
            EvidenceRecord(
                evidence_id=f"{chunk_id}_ev_{index:04d}",
                book_id="book_demo",
                chapter_id="ch_0001",
                chunk_id=chunk_id,
                quote_text=name,
                span_start=cursor,
                span_end=cursor + len(name),
                linked_object_type="mention",
                linked_object_id=mentions[-1].mention_id,
            )
        )
        cursor += len(name) + 1
    return NormalizedTextUnit(
        book_id="book_demo",
        chapter_id="ch_0001",
        chunk=ChunkRecord(chunk_id=chunk_id, chapter_id="ch_0001", chunk_index=1, text=" ".join(names), char_start=0, char_end=30),
        language=language,
        mentions=mentions,
        evidences=evidences,
        adapter_name="test",
    )


class MergeReviewTest(unittest.TestCase):
    def test_alias_merge_has_three_random_cases(self) -> None:
        rng = random.Random(1601)
        engine = AliasMergeEngine()
        for _ in range(3):
            alias = random.choice(["Alice", "Marcus", "Nora"])
            result = engine.merge("book_demo", "en", [_unit("ch_0001_ck_0001", "en", [f"{alias} Vale", alias])])
            self.assertGreaterEqual(len(result.characters), 1)
            self.assertTrue(result.characters[0].canonical_name)

    def test_review_queue_has_three_decision_cases(self) -> None:
        engine = AliasMergeEngine()
        result = engine.merge(
            "book_demo",
            "en",
            [
                _unit("ch_0001_ck_0001", "en", ["Alice Rowan", "Alice"]),
                _unit("ch_0001_ck_0002", "en", ["Marcus Vale", "Marcus"]),
                _unit("ch_0001_ck_0003", "en", ["Captain Nora", "Nora"]),
            ],
        )
        tasks = build_review_tasks("run_demo", result.characters, result.ambiguous_aliases)
        self.assertGreaterEqual(len(tasks), 3)
        self.assertTrue(all(task.status == "open" for task in tasks))

    def test_alias_merge_infers_english_title_role(self) -> None:
        engine = AliasMergeEngine()
        result = engine.merge("book_demo", "en", [_unit("ch_0001_ck_0001", "en", ["Captain Nora", "Captain Nora"])])
        self.assertIn("captain", result.characters[0].roles)
        self.assertIn("person", result.characters[0].roles)

    def test_alias_merge_infers_chinese_office_roles(self) -> None:
        engine = AliasMergeEngine()
        result = engine.merge("book_demo", "zh", [_unit("ch_0001_ck_0001", "zh", ["守门内侍"])])
        self.assertIn("guard", result.characters[0].roles)
        self.assertIn("attendant", result.characters[0].roles)


if __name__ == "__main__":
    unittest.main()
