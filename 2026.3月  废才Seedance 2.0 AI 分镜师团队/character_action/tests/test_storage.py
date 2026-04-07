from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from character_action.chunking import build_chunks, split_chapters
from character_action.ids import normalize_book_id
from character_action.models import BookRecord
from character_action.preprocess import route_adapter
from character_action.storage import SQLiteRepository


class StorageTest(unittest.TestCase):
    def test_sqlite_repository_roundtrip_has_three_cases(self) -> None:
        cases = [
            ("book_zh", "zh", "第1章 初见\n林晚看见顾昭。"),
            ("book_en", "en", "Chapter 1\nAlice Rowan met Marcus Vale."),
            ("book_mix", "en", "Chapter 1\nCaptain Nora saw Alice Rowan."),
        ]
        for raw_book_id, language, text in cases:
            with tempfile.TemporaryDirectory() as tmp:
                repo = SQLiteRepository(Path(tmp) / "store.sqlite3")
                repo.init_db()
                book_id = normalize_book_id(raw_book_id)
                chapters = split_chapters(book_id, text)
                adapter = route_adapter(language)
                units = []
                for chapter in chapters:
                    for chunk in build_chunks(chapter, 64, 8):
                        units.append(adapter.normalize_chunk(book_id, chapter.chapter_id, chunk, 12))
                repo.save_preprocess_result(
                    f"{book_id}-run",
                    BookRecord(book_id=book_id, title=book_id, language=language, author="", source_path="demo.txt", chapter_count=len(chapters)),
                    chapters,
                    units,
                )
                status = repo.load_status(book_id)
                self.assertTrue(status["book_exists"])
                self.assertGreaterEqual(status["chapter_count"], 1)
                self.assertGreaterEqual(status["chunk_count"], 1)
                self.assertEqual(status["relation_count"], 0)
                self.assertEqual(status["qa_finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
