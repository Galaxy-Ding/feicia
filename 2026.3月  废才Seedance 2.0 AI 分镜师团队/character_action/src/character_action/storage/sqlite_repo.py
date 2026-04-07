from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ..models import BookRecord, ChapterRecord, CharacterRecord, NormalizedTextUnit, QAFindingRecord, RelationRecord, ReviewTaskRecord


class SQLiteRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def init_db(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS books (
                    book_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    language TEXT NOT NULL,
                    author TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    chapter_count INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chapters (
                    book_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    chapter_index INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    PRIMARY KEY (book_id, chapter_id)
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    book_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    char_start INTEGER NOT NULL,
                    char_end INTEGER NOT NULL,
                    PRIMARY KEY (book_id, chunk_id)
                );
                CREATE TABLE IF NOT EXISTS mentions (
                    book_id TEXT NOT NULL,
                    mention_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    surface_form TEXT NOT NULL,
                    normalized_form TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    speaker_hint TEXT NOT NULL,
                    span_start INTEGER NOT NULL,
                    span_end INTEGER NOT NULL,
                    PRIMARY KEY (book_id, mention_id)
                );
                CREATE TABLE IF NOT EXISTS evidences (
                    book_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    quote_text TEXT NOT NULL,
                    span_start INTEGER NOT NULL,
                    span_end INTEGER NOT NULL,
                    linked_object_type TEXT NOT NULL,
                    linked_object_id TEXT NOT NULL,
                    PRIMARY KEY (book_id, evidence_id)
                );
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    run_id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    language TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stats_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS characters (
                    book_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    canonical_name TEXT NOT NULL,
                    aliases_json TEXT NOT NULL,
                    roles_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    mention_count INTEGER NOT NULL,
                    review_status TEXT NOT NULL,
                    PRIMARY KEY (book_id, character_id)
                );
                CREATE TABLE IF NOT EXISTS review_tasks (
                    book_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    review_patch_json TEXT NOT NULL,
                    PRIMARY KEY (book_id, task_id)
                );
                CREATE TABLE IF NOT EXISTS relations (
                    book_id TEXT NOT NULL,
                    relation_id TEXT NOT NULL,
                    source_character_id TEXT NOT NULL,
                    target_character_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    occurrence_count INTEGER NOT NULL,
                    review_status TEXT NOT NULL,
                    PRIMARY KEY (book_id, relation_id)
                );
                CREATE TABLE IF NOT EXISTS qa_findings (
                    book_id TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    finding_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    reason_codes_json TEXT NOT NULL,
                    message TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    PRIMARY KEY (book_id, finding_id)
                );
                """
            )

    def save_preprocess_result(
        self,
        run_id: str,
        book: BookRecord,
        chapters: list[ChapterRecord],
        normalized_units: list[NormalizedTextUnit],
    ) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO books(book_id, title, language, author, source_path, chapter_count)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id) DO UPDATE SET
                    title=excluded.title,
                    language=excluded.language,
                    author=excluded.author,
                    source_path=excluded.source_path,
                    chapter_count=excluded.chapter_count
                """,
                (book.book_id, book.title, book.language, book.author, book.source_path, book.chapter_count),
            )
            connection.executemany(
                """
                INSERT INTO chapters(book_id, chapter_id, chapter_index, title, raw_text)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(book_id, chapter_id) DO UPDATE SET
                    chapter_index=excluded.chapter_index,
                    title=excluded.title,
                    raw_text=excluded.raw_text
                """,
                [(item.book_id, item.chapter_id, item.chapter_index, item.title, item.raw_text) for item in chapters],
            )
            connection.executemany(
                """
                INSERT INTO chunks(book_id, chunk_id, chapter_id, chunk_index, text, char_start, char_end)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, chunk_id) DO UPDATE SET
                    chapter_id=excluded.chapter_id,
                    chunk_index=excluded.chunk_index,
                    text=excluded.text,
                    char_start=excluded.char_start,
                    char_end=excluded.char_end
                """,
                [
                    (
                        book.book_id,
                        unit.chunk.chunk_id,
                        unit.chunk.chapter_id,
                        unit.chunk.chunk_index,
                        unit.chunk.text,
                        unit.chunk.char_start,
                        unit.chunk.char_end,
                    )
                    for unit in normalized_units
                ],
            )
            connection.executemany(
                """
                INSERT INTO mentions(book_id, mention_id, chunk_id, surface_form, normalized_form, entity_type, speaker_hint, span_start, span_end)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, mention_id) DO UPDATE SET
                    chunk_id=excluded.chunk_id,
                    surface_form=excluded.surface_form,
                    normalized_form=excluded.normalized_form,
                    entity_type=excluded.entity_type,
                    speaker_hint=excluded.speaker_hint,
                    span_start=excluded.span_start,
                    span_end=excluded.span_end
                """,
                [
                    (
                        book.book_id,
                        mention.mention_id,
                        mention.chunk_id,
                        mention.surface_form,
                        mention.normalized_form,
                        mention.entity_type,
                        mention.speaker_hint,
                        mention.span_start,
                        mention.span_end,
                    )
                    for unit in normalized_units
                    for mention in unit.mentions
                ],
            )
            connection.executemany(
                """
                INSERT INTO evidences(book_id, evidence_id, chapter_id, chunk_id, quote_text, span_start, span_end, linked_object_type, linked_object_id)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, evidence_id) DO UPDATE SET
                    chapter_id=excluded.chapter_id,
                    chunk_id=excluded.chunk_id,
                    quote_text=excluded.quote_text,
                    span_start=excluded.span_start,
                    span_end=excluded.span_end,
                    linked_object_type=excluded.linked_object_type,
                    linked_object_id=excluded.linked_object_id
                """,
                [
                    (
                        evidence.book_id,
                        evidence.evidence_id,
                        evidence.chapter_id,
                        evidence.chunk_id,
                        evidence.quote_text,
                        evidence.span_start,
                        evidence.span_end,
                        evidence.linked_object_type,
                        evidence.linked_object_id,
                    )
                    for unit in normalized_units
                    for evidence in unit.evidences
                ],
            )
            stats = {
                "chapters": len(chapters),
                "chunks": len(normalized_units),
                "mentions": sum(len(unit.mentions) for unit in normalized_units),
                "evidences": sum(len(unit.evidences) for unit in normalized_units),
            }
            connection.execute(
                """
                INSERT INTO pipeline_runs(run_id, book_id, language, stage, status, stats_json)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    book_id=excluded.book_id,
                    language=excluded.language,
                    stage=excluded.stage,
                    status=excluded.status,
                    stats_json=excluded.stats_json
                """,
                (run_id, book.book_id, book.language, "preprocess", "success", json.dumps(stats, ensure_ascii=False)),
            )

    def save_character_results(
        self,
        run_id: str,
        book_id: str,
        language: str,
        characters: list[CharacterRecord],
        review_tasks: list[ReviewTaskRecord],
    ) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO characters(book_id, character_id, canonical_name, aliases_json, roles_json, summary, confidence, evidence_ids_json, mention_count, review_status)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, character_id) DO UPDATE SET
                    canonical_name=excluded.canonical_name,
                    aliases_json=excluded.aliases_json,
                    roles_json=excluded.roles_json,
                    summary=excluded.summary,
                    confidence=excluded.confidence,
                    evidence_ids_json=excluded.evidence_ids_json,
                    mention_count=excluded.mention_count,
                    review_status=excluded.review_status
                """,
                [
                    (
                        character.book_id,
                        character.character_id,
                        character.canonical_name,
                        json.dumps(character.aliases, ensure_ascii=False),
                        json.dumps(character.roles, ensure_ascii=False),
                        character.summary,
                        character.confidence,
                        json.dumps(character.evidence_ids, ensure_ascii=False),
                        character.mention_count,
                        character.review_status,
                    )
                    for character in characters
                ],
            )
            connection.executemany(
                """
                INSERT INTO review_tasks(book_id, task_id, run_id, task_type, target_id, reason_codes_json, status, review_patch_json)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, task_id) DO UPDATE SET
                    run_id=excluded.run_id,
                    task_type=excluded.task_type,
                    target_id=excluded.target_id,
                    reason_codes_json=excluded.reason_codes_json,
                    status=excluded.status,
                    review_patch_json=excluded.review_patch_json
                """,
                [
                    (
                        book_id,
                        task.task_id,
                        task.run_id,
                        task.task_type,
                        task.target_id,
                        json.dumps(task.reason_codes, ensure_ascii=False),
                        task.status,
                        json.dumps(task.review_patch, ensure_ascii=False),
                    )
                    for task in review_tasks
                ],
            )
            stats = {
                "characters": len(characters),
                "review_tasks": len(review_tasks),
            }
            connection.execute(
                """
                INSERT INTO pipeline_runs(run_id, book_id, language, stage, status, stats_json)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    book_id=excluded.book_id,
                    language=excluded.language,
                    stage=excluded.stage,
                    status=excluded.status,
                    stats_json=excluded.stats_json
                """,
                (run_id, book_id, language, "extract", "success", json.dumps(stats, ensure_ascii=False)),
            )

    def save_relation_results(
        self,
        run_id: str,
        book_id: str,
        language: str,
        relations: list[RelationRecord],
    ) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DELETE FROM relations WHERE book_id = ?", (book_id,))
            connection.executemany(
                """
                INSERT INTO relations(book_id, relation_id, source_character_id, target_character_id, relation_type, direction, confidence, evidence_ids_json, occurrence_count, review_status)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, relation_id) DO UPDATE SET
                    source_character_id=excluded.source_character_id,
                    target_character_id=excluded.target_character_id,
                    relation_type=excluded.relation_type,
                    direction=excluded.direction,
                    confidence=excluded.confidence,
                    evidence_ids_json=excluded.evidence_ids_json,
                    occurrence_count=excluded.occurrence_count,
                    review_status=excluded.review_status
                """,
                [
                    (
                        relation.book_id,
                        relation.relation_id,
                        relation.source_character_id,
                        relation.target_character_id,
                        relation.relation_type,
                        relation.direction,
                        relation.confidence,
                        json.dumps(relation.evidence_ids, ensure_ascii=False),
                        relation.occurrence_count,
                        relation.review_status,
                    )
                    for relation in relations
                ],
            )
            stats = {
                "relations": len(relations),
            }
            connection.execute(
                """
                INSERT INTO pipeline_runs(run_id, book_id, language, stage, status, stats_json)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    book_id=excluded.book_id,
                    language=excluded.language,
                    stage=excluded.stage,
                    status=excluded.status,
                    stats_json=excluded.stats_json
                """,
                (run_id, book_id, language, "relations", "success", json.dumps(stats, ensure_ascii=False)),
            )

    def save_qa_results(
        self,
        run_id: str,
        book_id: str,
        language: str,
        findings: list[QAFindingRecord],
        review_tasks: list[ReviewTaskRecord],
    ) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute("DELETE FROM qa_findings WHERE book_id = ?", (book_id,))
            connection.executemany(
                """
                INSERT INTO qa_findings(book_id, finding_id, run_id, finding_type, severity, target_type, target_id, reason_codes_json, message, evidence_ids_json, status)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, finding_id) DO UPDATE SET
                    run_id=excluded.run_id,
                    finding_type=excluded.finding_type,
                    severity=excluded.severity,
                    target_type=excluded.target_type,
                    target_id=excluded.target_id,
                    reason_codes_json=excluded.reason_codes_json,
                    message=excluded.message,
                    evidence_ids_json=excluded.evidence_ids_json,
                    status=excluded.status
                """,
                [
                    (
                        finding.book_id,
                        finding.finding_id,
                        finding.run_id,
                        finding.finding_type,
                        finding.severity,
                        finding.target_type,
                        finding.target_id,
                        json.dumps(finding.reason_codes, ensure_ascii=False),
                        finding.message,
                        json.dumps(finding.evidence_ids, ensure_ascii=False),
                        finding.status,
                    )
                    for finding in findings
                ],
            )
            connection.execute("DELETE FROM review_tasks WHERE book_id = ?", (book_id,))
            connection.executemany(
                """
                INSERT INTO review_tasks(book_id, task_id, run_id, task_type, target_id, reason_codes_json, status, review_patch_json)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id, task_id) DO UPDATE SET
                    run_id=excluded.run_id,
                    task_type=excluded.task_type,
                    target_id=excluded.target_id,
                    reason_codes_json=excluded.reason_codes_json,
                    status=excluded.status,
                    review_patch_json=excluded.review_patch_json
                """,
                [
                    (
                        book_id,
                        task.task_id,
                        task.run_id,
                        task.task_type,
                        task.target_id,
                        json.dumps(task.reason_codes, ensure_ascii=False),
                        task.status,
                        json.dumps(task.review_patch, ensure_ascii=False),
                    )
                    for task in review_tasks
                ],
            )
            stats = {
                "qa_findings": len(findings),
                "review_tasks": len(review_tasks),
            }
            connection.execute(
                """
                INSERT INTO pipeline_runs(run_id, book_id, language, stage, status, stats_json)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    book_id=excluded.book_id,
                    language=excluded.language,
                    stage=excluded.stage,
                    status=excluded.status,
                    stats_json=excluded.stats_json
                """,
                (run_id, book_id, language, "qa", "success", json.dumps(stats, ensure_ascii=False)),
            )

    def load_status(self, book_id: str | None = None) -> dict[str, Any]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            if book_id:
                row = connection.execute(
                    "SELECT * FROM books WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                if row is None:
                    return {"book_exists": False, "book_id": book_id}
                stats = connection.execute(
                    "SELECT COUNT(*) AS chunk_count FROM chunks WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                mentions = connection.execute(
                    "SELECT COUNT(*) AS mention_count FROM mentions WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                evidences = connection.execute(
                    "SELECT COUNT(*) AS evidence_count FROM evidences WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                characters = connection.execute(
                    "SELECT COUNT(*) AS character_count FROM characters WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                review_tasks = connection.execute(
                    "SELECT COUNT(*) AS review_task_count FROM review_tasks WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                qa_findings = connection.execute(
                    "SELECT COUNT(*) AS qa_finding_count FROM qa_findings WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                relations = connection.execute(
                    "SELECT COUNT(*) AS relation_count FROM relations WHERE book_id = ?",
                    (book_id,),
                ).fetchone()
                return {
                    "book_exists": True,
                    "book_id": row["book_id"],
                    "title": row["title"],
                    "language": row["language"],
                    "chapter_count": row["chapter_count"],
                    "chunk_count": stats["chunk_count"],
                    "mention_count": mentions["mention_count"],
                    "evidence_count": evidences["evidence_count"],
                    "character_count": characters["character_count"],
                    "relation_count": relations["relation_count"],
                    "qa_finding_count": qa_findings["qa_finding_count"],
                    "review_task_count": review_tasks["review_task_count"],
                }
            totals = {
                "books": connection.execute("SELECT COUNT(*) FROM books").fetchone()[0],
                "chapters": connection.execute("SELECT COUNT(*) FROM chapters").fetchone()[0],
                "chunks": connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
                "mentions": connection.execute("SELECT COUNT(*) FROM mentions").fetchone()[0],
                "evidences": connection.execute("SELECT COUNT(*) FROM evidences").fetchone()[0],
                "characters": connection.execute("SELECT COUNT(*) FROM characters").fetchone()[0],
                "relations": connection.execute("SELECT COUNT(*) FROM relations").fetchone()[0],
                "qa_findings": connection.execute("SELECT COUNT(*) FROM qa_findings").fetchone()[0],
                "review_tasks": connection.execute("SELECT COUNT(*) FROM review_tasks").fetchone()[0],
                "runs": connection.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0],
            }
            return totals
