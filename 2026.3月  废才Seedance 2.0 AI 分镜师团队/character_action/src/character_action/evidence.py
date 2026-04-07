from __future__ import annotations

from .ids import build_evidence_id
from .models import ChunkRecord, EvidenceRecord, MentionRecord


def build_evidence_for_mention(
    book_id: str,
    chapter_id: str,
    chunk: ChunkRecord,
    mention: MentionRecord,
    evidence_index: int,
    window: int,
) -> EvidenceRecord:
    if window <= 0:
        raise ValueError("window must be positive")
    left = max(0, mention.span_start - window)
    right = min(len(chunk.text), mention.span_end + window)
    quote_text = chunk.text[left:right].strip()
    return EvidenceRecord(
        evidence_id=build_evidence_id(chunk.chunk_id, evidence_index),
        book_id=book_id,
        chapter_id=chapter_id,
        chunk_id=chunk.chunk_id,
        quote_text=quote_text,
        span_start=chunk.char_start + mention.span_start,
        span_end=chunk.char_start + mention.span_end,
        linked_object_type="mention",
        linked_object_id=mention.mention_id,
    )
