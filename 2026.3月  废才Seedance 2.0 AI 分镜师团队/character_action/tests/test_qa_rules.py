from __future__ import annotations

import unittest

from character_action.models import CharacterRecord, RelationRecord
from character_action.review import QARuleEngine


def _character(character_id: str, name: str, *, aliases: list[str] | None = None, evidence_count: int = 2) -> CharacterRecord:
    return CharacterRecord(
        character_id=character_id,
        book_id="book_demo",
        canonical_name=name,
        aliases=aliases or [],
        roles=["person"],
        summary="demo",
        confidence=0.7,
        evidence_ids=[f"ev_{index:06d}" for index in range(1, evidence_count + 1)],
        mention_count=max(evidence_count, 1),
        review_status="auto_approved",
    )


def _relation(relation_id: str, source_id: str, target_id: str, *, relation_type: str = "interaction", confidence: float = 0.8, evidence_count: int = 2) -> RelationRecord:
    return RelationRecord(
        relation_id=relation_id,
        book_id="book_demo",
        source_character_id=source_id,
        target_character_id=target_id,
        relation_type=relation_type,
        direction="bidirectional",
        confidence=confidence,
        evidence_ids=[f"ev_rel_{index:06d}" for index in range(1, evidence_count + 1)],
        occurrence_count=max(evidence_count, 1),
        review_status="auto_approved",
    )


class QARulesTest(unittest.TestCase):
    def test_qa_rule_engine_flags_existing_rule_combinations(self) -> None:
        engine = QARuleEngine()
        cases = [
            (
                "en",
                [_character("char_000001", "she", evidence_count=1), _character("char_000002", "Marcus Vale")],
                [],
            ),
            (
                "en",
                [_character("char_000001", "Captain Nora", aliases=["Captain"]), _character("char_000002", "the Captain", aliases=["Captain"], evidence_count=1)],
                [_relation("rel_000001", "char_000001", "char_000002", confidence=0.64, evidence_count=1)],
            ),
        ]
        for language, characters, relations in cases:
            result = engine.run(run_id="run_demo", book_id="book_demo", language=language, characters=characters, relations=relations)
            self.assertGreaterEqual(len(result.findings), 1)
            self.assertGreaterEqual(len(result.review_tasks), 1)
            self.assertTrue(all(item.status == "open" for item in result.findings))
            self.assertTrue(all(item.status == "open" for item in result.review_tasks))

    def test_qa_rule_engine_flags_relation_type_conflict_for_incompatible_semantic_types(self) -> None:
        engine = QARuleEngine()
        result = engine.run(
            run_id="run_demo",
            book_id="book_demo",
            language="zh",
            characters=[_character("char_000001", "林晚"), _character("char_000002", "顾昭")],
            relations=[
                _relation("rel_000001", "char_000001", "char_000002", relation_type="family"),
                _relation("rel_000002", "char_000001", "char_000002", relation_type="hostile"),
            ],
        )
        self.assertIn("relation_type_conflict", {item.finding_type for item in result.findings})
        self.assertIn("relation_type_conflict", {item.task_type for item in result.review_tasks})

    def test_qa_rule_engine_ignores_dialogue_overlay_in_relation_conflict(self) -> None:
        engine = QARuleEngine()
        result = engine.run(
            run_id="run_demo",
            book_id="book_demo",
            language="zh",
            characters=[_character("char_000001", "林晚"), _character("char_000002", "顾昭")],
            relations=[
                _relation("rel_000001", "char_000001", "char_000002", relation_type="dialogue"),
                _relation("rel_000002", "char_000001", "char_000002", relation_type="hostile"),
            ],
        )
        self.assertNotIn("relation_type_conflict", {item.finding_type for item in result.findings})

    def test_qa_rule_engine_flags_character_attribute_conflict(self) -> None:
        engine = QARuleEngine()
        result = engine.run(
            run_id="run_demo",
            book_id="book_demo",
            language="en",
            characters=[_character("char_000001", "Sir Morgan", aliases=["Lady Morgan"])],
            relations=[],
        )
        self.assertIn("character_attribute_conflict", {item.finding_type for item in result.findings})
        self.assertIn("character_attribute_conflict", {item.task_type for item in result.review_tasks})


if __name__ == "__main__":
    unittest.main()
