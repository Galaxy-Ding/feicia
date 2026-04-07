from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .chunking import build_chunks, split_chapters
from .config import RuntimeConfig, ensure_project_layout, ensure_within_root, load_config
from .extractors import AliasMergeEngine, DualLLMCharacterExtractor, RelationEngine
from .ids import build_review_task_id, normalize_book_id
from .llm_client import LLMModelSettings, RoutedOpenAICompatibleClient, default_local_provider_config, load_local_providers
from .logging_utils import append_jsonl
from .models import BookRecord, CharacterRecord, ChunkRecord, EvidenceRecord, MentionRecord, NormalizedTextUnit, QAFindingRecord, RelationRecord, ReviewTaskRecord
from .preprocess import route_adapter
from .review import QARuleEngine, build_review_tasks
from .schema_tools import SchemaValidator
from .storage import SQLiteRepository


class CharacterActionPipeline:
    def __init__(self, project_root: Path, config_path: str | Path = "configs/dev.yaml", llm_client=None) -> None:
        self.config: RuntimeConfig = load_config(project_root, config_path)
        self.repo = SQLiteRepository(self.config.sqlite_path)
        self.validator = SchemaValidator(self.config.project_root / "schemas")
        self.alias_merge_engine = AliasMergeEngine()
        self.relation_engine = RelationEngine()
        self.qa_rule_engine = QARuleEngine()
        self.llm_client = llm_client

    def prepare(self) -> dict[str, object]:
        created = ensure_project_layout(self.config)
        self.repo.init_db()
        payload = {
            "project_root": str(self.config.project_root),
            "config_path": str(self.config.config_path),
            "created": [str(path) for path in created],
            "sqlite_path": str(self.config.sqlite_path),
            "adapter_mode": self.config.adapter_mode,
        }
        append_jsonl(self.config.data.logs / "run-log.jsonl", {"event": "prepare", **payload})
        return payload

    def doctor(self) -> dict[str, object]:
        status = {
            "adapter_mode": self.config.adapter_mode,
            "hanlp": self._module_status("hanlp"),
            "booknlp": self._module_status("booknlp.booknlp"),
        }
        append_jsonl(self.config.data.logs / "run-log.jsonl", {"event": "doctor", **status})
        return status

    def preprocess_book(
        self,
        *,
        book_id: str,
        title: str,
        language: str,
        input_path: str | Path,
        author: str = "",
        engine_mode: str | None = None,
    ) -> dict[str, object]:
        if not title.strip():
            raise ValueError("title must be non-empty")
        normalized_book_id = normalize_book_id(book_id)
        self.prepare()
        source = Path(input_path)
        source_path = ensure_within_root(
            self.config.project_root,
            source if source.is_absolute() else self.config.project_root / source,
        )
        effective_mode = (engine_mode or self.config.adapter_mode).strip().lower()
        adapter = route_adapter(
            language,
            engine_mode=effective_mode,
            model_name=self.config.hanlp_model if language.strip().lower() == "zh" else self.config.booknlp_model,
            native_temp_root=self.config.native_temp_root,
            pipeline_name=self.config.booknlp_pipeline,
        )
        raw_text = source_path.read_text(encoding="utf-8")
        chapters = split_chapters(normalized_book_id, raw_text)
        normalized_units = []
        for chapter in chapters:
            for chunk in build_chunks(chapter, self.config.chunk_size, self.config.chunk_overlap):
                normalized_units.append(adapter.normalize_chunk(normalized_book_id, chapter.chapter_id, chunk, self.config.evidence_window))
        book = BookRecord(
            book_id=normalized_book_id,
            title=title.strip(),
            language=language.strip().lower(),
            author=author.strip(),
            source_path=str(source_path.relative_to(self.config.project_root)).replace("\\", "/"),
            chapter_count=len(chapters),
        )
        self.validator.validate("book.schema.json", book.to_dict())
        for chapter in chapters:
            self.validator.validate("chapter.schema.json", chapter.to_dict())
        for unit in normalized_units:
            for evidence in unit.evidences:
                self.validator.validate("evidence.schema.json", evidence.to_dict())
        run_id = f"{normalized_book_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.repo.save_preprocess_result(run_id, book, chapters, normalized_units)
        export_payload = {
            "run_id": run_id,
            "book": book.to_dict(),
            "chapters": [chapter.to_dict() for chapter in chapters],
            "normalized_units": [unit.to_dict() for unit in normalized_units],
        }
        export_path = self.config.data.normalized / f"{normalized_book_id}.json"
        export_path.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        append_jsonl(
            self.config.data.logs / "run-log.jsonl",
            {
                "event": "preprocess_book",
                "run_id": run_id,
                "book_id": normalized_book_id,
                "language": language.strip().lower(),
                "normalized_path": str(export_path),
                "adapter_name": adapter.adapter_name,
            },
        )
        return {
            "run_id": run_id,
            "book_id": normalized_book_id,
            "language": language.strip().lower(),
            "chapter_count": len(chapters),
            "chunk_count": len(normalized_units),
            "mention_count": sum(len(unit.mentions) for unit in normalized_units),
            "evidence_count": sum(len(unit.evidences) for unit in normalized_units),
            "normalized_path": str(export_path),
            "sqlite_path": str(self.config.sqlite_path),
            "adapter_name": adapter.adapter_name,
            "engine_mode": effective_mode,
        }

    def extract_characters(self, *, book_id: str) -> dict[str, object]:
        normalized_book_id = normalize_book_id(book_id)
        self.prepare()
        payload, book_payload, units = self._load_normalized_book(normalized_book_id)
        merge_result = self.alias_merge_engine.merge(normalized_book_id, str(book_payload["language"]), units)
        review_tasks = build_review_tasks(payload["run_id"], merge_result.characters, merge_result.ambiguous_aliases)
        return self._export_character_results(
            run_id=str(payload["run_id"]),
            book_id=normalized_book_id,
            language=str(book_payload["language"]),
            book_payload=book_payload,
            characters=merge_result.characters,
            review_tasks=review_tasks,
            event="extract_characters",
        )

    def extract_characters_llm(
        self,
        *,
        book_id: str,
        llm_config_path: str | Path | None = None,
        extractor_provider: str = "codex",
        extractor_model: str = "gpt-5.4",
        reviewer_provider: str = "claude",
        reviewer_model: str = "gpt-5.4",
    ) -> dict[str, object]:
        normalized_book_id = normalize_book_id(book_id)
        self.prepare()
        payload, book_payload, units = self._load_normalized_book(normalized_book_id)
        llm_client = self.llm_client or self._build_llm_client(llm_config_path)
        extractor = DualLLMCharacterExtractor(
            llm_client,
            extractor_model=LLMModelSettings(
                name=extractor_model,
                provider=extractor_provider,
                temperature=0.2,
                max_tokens=6000,
            ),
            reviewer_model=LLMModelSettings(
                name=reviewer_model,
                provider=reviewer_provider,
                temperature=0.1,
                max_tokens=8000,
            ),
        )
        llm_result = extractor.extract(
            book_id=normalized_book_id,
            language=str(book_payload["language"]),
            units=units,
        )
        review_tasks = build_review_tasks(payload["run_id"], llm_result.characters, llm_result.ambiguous_aliases)
        export_payload = self._export_character_results(
            run_id=str(payload["run_id"]),
            book_id=normalized_book_id,
            language=str(book_payload["language"]),
            book_payload=book_payload,
            characters=llm_result.characters,
            review_tasks=review_tasks,
            event="extract_characters_llm",
        )
        export_root = self.config.data.exports / normalized_book_id
        candidates_path = export_root / "llm_character_candidates.json"
        review_path = export_root / "llm_character_review.json"
        candidates_path.write_text(
            json.dumps(
                {
                    "run_id": payload["run_id"],
                    "book_id": normalized_book_id,
                    "extractor_provider": extractor_provider,
                    "extractor_model": extractor_model,
                    "chunk_candidates": llm_result.chunk_candidates,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        review_path.write_text(
            json.dumps(
                {
                    "run_id": payload["run_id"],
                    "book_id": normalized_book_id,
                    "reviewer_provider": reviewer_provider,
                    "reviewer_model": reviewer_model,
                    "payload": llm_result.reviewer_payload,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        append_jsonl(
            self.config.data.logs / "run-log.jsonl",
            {
                "event": "extract_characters_llm_artifacts",
                "run_id": payload["run_id"],
                "book_id": normalized_book_id,
                "llm_character_candidates_path": str(candidates_path),
                "llm_character_review_path": str(review_path),
            },
        )
        export_payload.update(
            {
                "extractor_provider": extractor_provider,
                "extractor_model": extractor_model,
                "reviewer_provider": reviewer_provider,
                "reviewer_model": reviewer_model,
                "llm_character_candidates_path": str(candidates_path),
                "llm_character_review_path": str(review_path),
            }
        )
        return export_payload

    def status(self, book_id: str | None = None) -> dict[str, object]:
        self.prepare()
        if book_id:
            return self.repo.load_status(normalize_book_id(book_id))
        return self.repo.load_status()

    def _export_character_results(
        self,
        *,
        run_id: str,
        book_id: str,
        language: str,
        book_payload: dict[str, object],
        characters: list[CharacterRecord],
        review_tasks: list[ReviewTaskRecord],
        event: str,
    ) -> dict[str, object]:
        for character in characters:
            self.validator.validate("character.schema.json", character.to_dict())
        for task in review_tasks:
            self.validator.validate("review_task.schema.json", task.to_dict())
        export_root = self.config.data.exports / book_id
        export_root.mkdir(parents=True, exist_ok=True)
        characters_path = export_root / "character_cards.json"
        review_path = export_root / "review_queue.json"
        characters_payload = {
            "run_id": run_id,
            "book": book_payload,
            "characters": [item.to_dict() for item in characters],
        }
        review_payload = {
            "run_id": run_id,
            "book_id": book_id,
            "tasks": [item.to_dict() for item in review_tasks],
        }
        characters_path.write_text(json.dumps(characters_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        review_path.write_text(json.dumps(review_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.repo.save_character_results(run_id, book_id, language, characters, review_tasks)
        append_jsonl(
            self.config.data.logs / "run-log.jsonl",
            {
                "event": event,
                "run_id": run_id,
                "book_id": book_id,
                "characters_path": str(characters_path),
                "review_queue_path": str(review_path),
            },
        )
        return {
            "run_id": run_id,
            "book_id": book_id,
            "character_count": len(characters),
            "review_task_count": len(review_tasks),
            "characters_path": str(characters_path),
            "review_queue_path": str(review_path),
        }

    def build_relations(self, *, book_id: str) -> dict[str, object]:
        normalized_book_id = normalize_book_id(book_id)
        self.prepare()
        normalized_path = self.config.data.normalized / f"{normalized_book_id}.json"
        characters_path = self.config.data.exports / normalized_book_id / "character_cards.json"
        payload = json.loads(normalized_path.read_text(encoding="utf-8"))
        character_payload = json.loads(characters_path.read_text(encoding="utf-8"))
        book_payload = payload["book"]
        units = [self._unit_from_dict(item) for item in payload["normalized_units"]]
        characters = [self._character_from_dict(item) for item in character_payload["characters"]]
        relation_result = self.relation_engine.build(normalized_book_id, str(book_payload["language"]), characters, units)
        for relation in relation_result.relations:
            self.validator.validate("relation.schema.json", relation.to_dict())
        export_root = self.config.data.exports / normalized_book_id
        export_root.mkdir(parents=True, exist_ok=True)
        relation_path = export_root / "relation_graph.json"
        relation_payload = {
            "run_id": payload["run_id"],
            "book": book_payload,
            "relations": [item.to_dict() for item in relation_result.relations],
        }
        relation_path.write_text(json.dumps(relation_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.repo.save_relation_results(payload["run_id"], normalized_book_id, str(book_payload["language"]), relation_result.relations)
        append_jsonl(
            self.config.data.logs / "run-log.jsonl",
            {
                "event": "build_relations",
                "run_id": payload["run_id"],
                "book_id": normalized_book_id,
                "relation_graph_path": str(relation_path),
            },
        )
        return {
            "run_id": payload["run_id"],
            "book_id": normalized_book_id,
            "relation_count": len(relation_result.relations),
            "relation_graph_path": str(relation_path),
        }

    def run_qa(self, *, book_id: str) -> dict[str, object]:
        normalized_book_id = normalize_book_id(book_id)
        self.prepare()
        normalized_path = self.config.data.normalized / f"{normalized_book_id}.json"
        export_root = self.config.data.exports / normalized_book_id
        characters_path = export_root / "character_cards.json"
        relations_path = export_root / "relation_graph.json"
        review_path = export_root / "review_queue.json"
        payload = json.loads(normalized_path.read_text(encoding="utf-8"))
        character_payload = json.loads(characters_path.read_text(encoding="utf-8"))
        review_payload = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else {"tasks": []}
        relation_payload = json.loads(relations_path.read_text(encoding="utf-8")) if relations_path.exists() else {"relations": []}
        book_payload = payload["book"]
        characters = [self._character_from_dict(item) for item in character_payload.get("characters", [])]
        relations = [self._relation_from_dict(item) for item in relation_payload.get("relations", [])]
        existing_tasks = [ReviewTaskRecord(**item) for item in review_payload.get("tasks", [])]
        qa_result = self.qa_rule_engine.run(
            run_id=str(payload["run_id"]),
            book_id=normalized_book_id,
            language=str(book_payload["language"]),
            characters=characters,
            relations=relations,
        )
        merged_tasks = self._merge_review_tasks(existing_tasks, qa_result.review_tasks, run_id=str(payload["run_id"]))
        for finding in qa_result.findings:
            self.validator.validate("qa_finding.schema.json", finding.to_dict())
        for task in merged_tasks:
            self.validator.validate("review_task.schema.json", task.to_dict())
        findings_path = export_root / "qa_findings.json"
        findings_payload = {
            "run_id": payload["run_id"],
            "book": book_payload,
            "findings": [item.to_dict() for item in qa_result.findings],
        }
        updated_review_payload = {
            "run_id": payload["run_id"],
            "book_id": normalized_book_id,
            "tasks": [item.to_dict() for item in merged_tasks],
        }
        findings_path.write_text(json.dumps(findings_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        review_path.write_text(json.dumps(updated_review_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.repo.save_qa_results(str(payload["run_id"]), normalized_book_id, str(book_payload["language"]), qa_result.findings, merged_tasks)
        append_jsonl(
            self.config.data.logs / "run-log.jsonl",
            {
                "event": "run_qa",
                "run_id": payload["run_id"],
                "book_id": normalized_book_id,
                "qa_findings_path": str(findings_path),
                "review_queue_path": str(review_path),
            },
        )
        return {
            "run_id": payload["run_id"],
            "book_id": normalized_book_id,
            "qa_finding_count": len(qa_result.findings),
            "review_task_count": len(merged_tasks),
            "qa_findings_path": str(findings_path),
            "review_queue_path": str(review_path),
        }

    def _module_status(self, module_name: str) -> dict[str, object]:
        try:
            module = __import__(module_name, fromlist=["dummy"])
            return {"available": True, "version": getattr(module, "__version__", "unknown")}
        except Exception as exc:
            return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    def _load_normalized_book(self, normalized_book_id: str) -> tuple[dict[str, object], dict[str, object], list[NormalizedTextUnit]]:
        normalized_path = self.config.data.normalized / f"{normalized_book_id}.json"
        payload = json.loads(normalized_path.read_text(encoding="utf-8"))
        book_payload = payload["book"]
        units = [self._unit_from_dict(item) for item in payload["normalized_units"]]
        return payload, book_payload, units

    def _build_llm_client(self, llm_config_path: str | Path | None):
        path = Path(llm_config_path).resolve() if llm_config_path else default_local_provider_config(self.config.project_root)
        if not path.exists():
            raise FileNotFoundError(f"LLM provider config not found: {path}")
        return RoutedOpenAICompatibleClient(load_local_providers(path))

    def _unit_from_dict(self, payload: dict[str, object]) -> NormalizedTextUnit:
        chunk_payload = payload["chunk"]
        chunk = ChunkRecord(**chunk_payload)
        mentions = [MentionRecord(**item) for item in payload.get("mentions", [])]
        evidences = [EvidenceRecord(**item) for item in payload.get("evidences", [])]
        return NormalizedTextUnit(
            book_id=str(payload["book_id"]),
            chapter_id=str(payload["chapter_id"]),
            chunk=chunk,
            language=str(payload["language"]),
            sentences=[str(item) for item in payload.get("sentences", [])],
            mentions=mentions,
            evidences=evidences,
            adapter_name=str(payload.get("adapter_name", "")),
        )

    def _character_from_dict(self, payload: dict[str, object]) -> CharacterRecord:
        return CharacterRecord(
            character_id=str(payload["character_id"]),
            book_id=str(payload["book_id"]),
            canonical_name=str(payload["canonical_name"]),
            aliases=[str(item) for item in payload.get("aliases", [])],
            roles=[str(item) for item in payload.get("roles", [])],
            summary=str(payload.get("summary", "")),
            confidence=float(payload.get("confidence", 0.0)),
            evidence_ids=[str(item) for item in payload.get("evidence_ids", [])],
            mention_count=int(payload.get("mention_count", 0)),
            review_status=str(payload.get("review_status", "pending")),
        )

    def _relation_from_dict(self, payload: dict[str, object]) -> RelationRecord:
        return RelationRecord(
            relation_id=str(payload["relation_id"]),
            book_id=str(payload["book_id"]),
            source_character_id=str(payload["source_character_id"]),
            target_character_id=str(payload["target_character_id"]),
            relation_type=str(payload["relation_type"]),
            direction=str(payload["direction"]),
            confidence=float(payload.get("confidence", 0.0)),
            evidence_ids=[str(item) for item in payload.get("evidence_ids", [])],
            occurrence_count=int(payload.get("occurrence_count", 0)),
            review_status=str(payload.get("review_status", "pending")),
        )

    def _merge_review_tasks(
        self,
        existing_tasks: list[ReviewTaskRecord],
        qa_tasks: list[ReviewTaskRecord],
        *,
        run_id: str,
    ) -> list[ReviewTaskRecord]:
        merged: list[ReviewTaskRecord] = []
        seen: set[tuple[str, str, tuple[str, ...]]] = set()
        for task in [*existing_tasks, *qa_tasks]:
            key = (task.task_type, task.target_id, tuple(sorted(task.reason_codes)))
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                ReviewTaskRecord(
                    task_id="",
                    run_id=run_id,
                    task_type=task.task_type,
                    target_id=task.target_id,
                    reason_codes=list(task.reason_codes),
                    status=task.status,
                    review_patch=dict(task.review_patch),
                )
            )
        for index, task in enumerate(merged, start=1):
            task.task_id = build_review_task_id(index)
        return merged
