from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from character_action.schema_tools import SchemaValidationError, SchemaValidator


class SchemaToolsTest(unittest.TestCase):
    def test_schema_validator_accepts_three_core_payloads(self) -> None:
        root = Path(__file__).resolve().parents[1] / "schemas"
        validator = SchemaValidator(root)
        validator.validate("book.schema.json", {"book_id": "book_demo", "title": "Demo", "language": "zh", "author": "", "source_path": "a.txt", "chapter_count": 1})
        validator.validate("character.schema.json", {"character_id": "char_000001", "book_id": "book_demo", "canonical_name": "林晚", "aliases": ["晚晚"], "roles": ["person"], "summary": "Demo", "confidence": 0.7})
        validator.validate("review_task.schema.json", {"task_id": "review_000001", "run_id": "run_1", "task_type": "demo", "target_id": "char_1", "reason_codes": ["X"], "status": "open", "review_patch": {}})
        validator.validate("qa_finding.schema.json", {"finding_id": "qa_000001", "run_id": "run_1", "book_id": "book_demo", "finding_type": "demo", "severity": "medium", "target_type": "character", "target_id": "char_1", "reason_codes": ["X"], "message": "demo", "status": "open"})

    def test_schema_validator_rejects_missing_required_field(self) -> None:
        root = Path(__file__).resolve().parents[1] / "schemas"
        validator = SchemaValidator(root)
        with self.assertRaises(SchemaValidationError):
            validator.validate("book.schema.json", {"book_id": "book_demo"})


if __name__ == "__main__":
    unittest.main()
