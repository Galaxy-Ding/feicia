from __future__ import annotations

import re

from .ids import build_chapter_id, build_chunk_id
from .models import ChapterRecord, ChunkRecord

_CHAPTER_RE = re.compile(r"(?m)^(?:#{1,6}\s*)?((?:第[^\n]{1,20}章|Chapter\s+\d+|CHAPTER\s+\d+)(?:[ \t]+[^\n]+)?)$")


def split_chapters(book_id: str, text: str) -> list[ChapterRecord]:
    content = text.strip()
    if not content:
        raise ValueError("book text is empty")
    matches = list(_CHAPTER_RE.finditer(content))
    if not matches:
        return [ChapterRecord(chapter_id=build_chapter_id(1), book_id=book_id, chapter_index=1, title="chapter_1", raw_text=content)]
    chapters: list[ChapterRecord] = []
    for index, match in enumerate(matches, start=1):
        start = match.end()
        end = matches[index].start() if index < len(matches) else len(content)
        heading = match.group(1).strip() or f"chapter_{index}"
        raw_text = content[start:end].strip()
        if not raw_text:
            continue
        chapters.append(
            ChapterRecord(
                chapter_id=build_chapter_id(index),
                book_id=book_id,
                chapter_index=index,
                title=heading,
                raw_text=raw_text,
            )
        )
    return chapters or [ChapterRecord(chapter_id=build_chapter_id(1), book_id=book_id, chapter_index=1, title="chapter_1", raw_text=content)]


def build_chunks(chapter: ChapterRecord, chunk_size: int, overlap: int) -> list[ChunkRecord]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")
    chunks: list[ChunkRecord] = []
    text = chapter.raw_text
    cursor = 0
    chunk_index = 1
    step = chunk_size - overlap
    while cursor < len(text):
        end = min(len(text), cursor + chunk_size)
        chunk_text = text[cursor:end].strip()
        if chunk_text:
            left_trim = len(text[cursor:end]) - len(text[cursor:end].lstrip())
            right_trim = len(text[cursor:end].rstrip())
            char_start = cursor + left_trim
            char_end = cursor + right_trim
            chunks.append(
                ChunkRecord(
                    chunk_id=build_chunk_id(chapter.chapter_index, chunk_index),
                    chapter_id=chapter.chapter_id,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    char_start=char_start,
                    char_end=char_end,
                )
            )
            chunk_index += 1
        if end == len(text):
            break
        cursor += step
    return chunks
