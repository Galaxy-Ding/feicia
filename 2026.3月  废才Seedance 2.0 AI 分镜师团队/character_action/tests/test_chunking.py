from __future__ import annotations

import random
import unittest

from character_action.chunking import build_chunks, split_chapters
from character_action.evidence import build_evidence_for_mention
from character_action.ids import build_mention_id, normalize_book_id
from character_action.models import ChunkRecord, MentionRecord


class ChunkingTest(unittest.TestCase):
    def test_split_chapters_has_three_random_heading_cases(self) -> None:
        rng = random.Random(1101)
        for _ in range(3):
            number = rng.randint(2, 5)
            text = "\n".join(f"Chapter {index}\nBody {index} Alice Rowan appears." for index in range(1, number + 1))
            chapters = split_chapters(normalize_book_id("demo"), text)
            self.assertEqual(len(chapters), number)
            self.assertTrue(all(item.chapter_id.startswith("ch_") for item in chapters))

    def test_build_chunks_has_three_random_size_cases(self) -> None:
        rng = random.Random(1102)
        chapter = split_chapters(normalize_book_id("demo"), "Chapter 1\n" + ("abcdefghi " * 90))[0]
        for _ in range(3):
            chunk_size = rng.randint(40, 70)
            overlap = rng.randint(5, 15)
            chunks = build_chunks(chapter, chunk_size, overlap)
            self.assertGreaterEqual(len(chunks), 2)
            self.assertTrue(all(item.char_end > item.char_start for item in chunks))

    def test_build_evidence_for_mention_has_three_random_windows(self) -> None:
        chunk = ChunkRecord(
            chunk_id="ch_0001_ck_0001",
            chapter_id="ch_0001",
            chunk_index=1,
            text="Alice Rowan met Marcus Vale near the gate.",
            char_start=100,
            char_end=142,
        )
        mention = MentionRecord(
            mention_id=build_mention_id(chunk.chunk_id, 1),
            chunk_id=chunk.chunk_id,
            surface_form="Marcus Vale",
            normalized_form="marcus vale",
            entity_type="person",
            speaker_hint="",
            span_start=17,
            span_end=28,
        )
        for index, window in enumerate((6, 12, 18), start=1):
            evidence = build_evidence_for_mention("book_demo", "ch_0001", chunk, mention, index, window)
            self.assertEqual(evidence.span_start, 117)
            self.assertEqual(evidence.span_end, 128)
            self.assertIn("Marcus Vale", evidence.quote_text)


if __name__ == "__main__":
    unittest.main()
