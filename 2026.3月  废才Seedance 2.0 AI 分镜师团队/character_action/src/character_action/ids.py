from __future__ import annotations

import re


def normalize_book_id(raw: str) -> str:
    text = raw.strip().lower().replace(" ", "_")
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        raise ValueError("book_id must contain at least one ascii letter or digit")
    return text if text.startswith("book_") else f"book_{text}"


def build_chapter_id(chapter_index: int) -> str:
    if chapter_index <= 0:
        raise ValueError("chapter_index must be positive")
    return f"ch_{chapter_index:04d}"


def build_chunk_id(chapter_index: int, chunk_index: int) -> str:
    if chunk_index <= 0:
        raise ValueError("chunk_index must be positive")
    return f"{build_chapter_id(chapter_index)}_ck_{chunk_index:04d}"


def build_mention_id(chunk_id: str, mention_index: int) -> str:
    if mention_index <= 0:
        raise ValueError("mention_index must be positive")
    return f"{chunk_id}_mn_{mention_index:04d}"


def build_evidence_id(chunk_id: str, evidence_index: int) -> str:
    if evidence_index <= 0:
        raise ValueError("evidence_index must be positive")
    return f"{chunk_id}_ev_{evidence_index:04d}"


def build_character_id(character_index: int) -> str:
    if character_index <= 0:
        raise ValueError("character_index must be positive")
    return f"char_{character_index:06d}"


def build_relation_id(relation_index: int) -> str:
    if relation_index <= 0:
        raise ValueError("relation_index must be positive")
    return f"rel_{relation_index:06d}"


def build_qa_finding_id(finding_index: int) -> str:
    if finding_index <= 0:
        raise ValueError("finding_index must be positive")
    return f"qa_{finding_index:06d}"


def build_review_task_id(task_index: int) -> str:
    if task_index <= 0:
        raise ValueError("task_index must be positive")
    return f"review_{task_index:06d}"
