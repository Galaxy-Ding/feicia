from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class BookRecord:
    book_id: str
    title: str
    language: str
    author: str
    source_path: str
    chapter_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChapterRecord:
    chapter_id: str
    book_id: str
    chapter_index: int
    title: str
    raw_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    chapter_id: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MentionRecord:
    mention_id: str
    chunk_id: str
    surface_form: str
    normalized_form: str
    entity_type: str
    speaker_hint: str
    span_start: int
    span_end: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceRecord:
    evidence_id: str
    book_id: str
    chapter_id: str
    chunk_id: str
    quote_text: str
    span_start: int
    span_end: int
    linked_object_type: str
    linked_object_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CharacterRecord:
    character_id: str
    book_id: str
    canonical_name: str
    aliases: list[str]
    roles: list[str]
    summary: str
    confidence: float
    evidence_ids: list[str] = field(default_factory=list)
    mention_count: int = 0
    review_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RelationRecord:
    relation_id: str
    book_id: str
    source_character_id: str
    target_character_id: str
    relation_type: str
    direction: str
    confidence: float
    evidence_ids: list[str] = field(default_factory=list)
    occurrence_count: int = 0
    review_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QAFindingRecord:
    finding_id: str
    run_id: str
    book_id: str
    finding_type: str
    severity: str
    target_type: str
    target_id: str
    reason_codes: list[str]
    message: str
    evidence_ids: list[str] = field(default_factory=list)
    status: str = "open"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReviewTaskRecord:
    task_id: str
    run_id: str
    task_type: str
    target_id: str
    reason_codes: list[str]
    status: str
    review_patch: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NormalizedTextUnit:
    book_id: str
    chapter_id: str
    chunk: ChunkRecord
    language: str
    sentences: list[str] = field(default_factory=list)
    mentions: list[MentionRecord] = field(default_factory=list)
    evidences: list[EvidenceRecord] = field(default_factory=list)
    adapter_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "book_id": self.book_id,
            "chapter_id": self.chapter_id,
            "chunk": self.chunk.to_dict(),
            "language": self.language,
            "sentences": list(self.sentences),
            "mentions": [item.to_dict() for item in self.mentions],
            "evidences": [item.to_dict() for item in self.evidences],
            "adapter_name": self.adapter_name,
        }
