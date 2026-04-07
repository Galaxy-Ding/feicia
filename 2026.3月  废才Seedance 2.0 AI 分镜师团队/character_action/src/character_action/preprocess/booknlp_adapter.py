from __future__ import annotations

import csv
import importlib
import re
import tempfile
from pathlib import Path
from typing import Any

from ..evidence import build_evidence_for_mention
from ..ids import build_mention_id
from ..models import ChunkRecord, MentionRecord, NormalizedTextUnit
from .text_utils import normalize_text

_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]?")
_STOPWORDS = {"Chapter", "He", "She", "They", "The", "A", "An", "In", "On", "At"}


class BookNLPAdapter:
    def __init__(
        self,
        *,
        engine_mode: str = "auto",
        model_name: str | None = None,
        pipeline_name: str | None = None,
        native_temp_root=None,
    ) -> None:
        self.engine_mode = engine_mode
        self.model_name = model_name or "small"
        self.pipeline_name = pipeline_name or "entity,quote"
        self.native_temp_root = native_temp_root
        self.adapter_name = "booknlp_fallback"

    def normalize_chunk(self, book_id: str, chapter_id: str, chunk: ChunkRecord, evidence_window: int) -> NormalizedTextUnit:
        if self.engine_mode != "fallback":
            try:
                return self._normalize_chunk_native(book_id, chapter_id, chunk, evidence_window)
            except Exception:
                if self.engine_mode == "native":
                    raise
        mentions: list[MentionRecord] = []
        evidences = []
        seen_spans: set[tuple[int, int]] = set()
        for match in _NAME_RE.finditer(chunk.text):
            surface = match.group(1)
            if surface in _STOPWORDS:
                continue
            span = (match.start(1), match.end(1))
            if span in seen_spans:
                continue
            seen_spans.add(span)
            mention = MentionRecord(
                mention_id=build_mention_id(chunk.chunk_id, len(mentions) + 1),
                chunk_id=chunk.chunk_id,
                surface_form=surface,
                normalized_form=surface.lower(),
                entity_type="person",
                speaker_hint=_guess_speaker_hint(chunk.text, span[0]),
                span_start=span[0],
                span_end=span[1],
            )
            mentions.append(mention)
            evidences.append(build_evidence_for_mention(book_id, chapter_id, chunk, mention, len(evidences) + 1, evidence_window))
        return NormalizedTextUnit(
            book_id=book_id,
            chapter_id=chapter_id,
            chunk=chunk,
            language="en",
            sentences=[normalize_text(item.group(0)) for item in _SENTENCE_RE.finditer(chunk.text) if normalize_text(item.group(0))],
            mentions=mentions,
            evidences=evidences,
            adapter_name=self.adapter_name,
        )

    def _normalize_chunk_native(self, book_id: str, chapter_id: str, chunk: ChunkRecord, evidence_window: int) -> NormalizedTextUnit:
        booknlp_module = importlib.import_module("booknlp.booknlp")
        booknlp_cls = getattr(booknlp_module, "BookNLP")
        with tempfile.TemporaryDirectory(dir=self.native_temp_root) as tmp:
            root = Path(tmp)
            input_path = root / "chunk.txt"
            output_root = root / "output"
            input_path.write_text(chunk.text, encoding="utf-8")
            model_params = {"pipeline": self.pipeline_name, "model": self.model_name}
            booknlp = booknlp_cls("en", model_params)
            booknlp.process(str(input_path), str(output_root), "chunk")
            mentions = self._load_native_mentions(chunk, output_root / "chunk.entities", output_root / "chunk.quotes")
        if not mentions:
            raise RuntimeError("BookNLP native output did not yield person mentions")
        evidences = [
            build_evidence_for_mention(book_id, chapter_id, chunk, mention, index, evidence_window)
            for index, mention in enumerate(mentions, start=1)
        ]
        self.adapter_name = f"booknlp_native:{self.model_name}"
        return NormalizedTextUnit(
            book_id=book_id,
            chapter_id=chapter_id,
            chunk=chunk,
            language="en",
            sentences=[normalize_text(item.group(0)) for item in _SENTENCE_RE.finditer(chunk.text) if normalize_text(item.group(0))],
            mentions=mentions,
            evidences=evidences,
            adapter_name=self.adapter_name,
        )

    def _load_native_mentions(self, chunk: ChunkRecord, entities_path: Path, quotes_path: Path) -> list[MentionRecord]:
        quote_hints = _load_quote_hints(quotes_path)
        mentions: list[MentionRecord] = []
        search_cursor = 0
        if not entities_path.exists():
            return mentions
        with entities_path.open("r", encoding="utf-8") as handle:
            reader = csv.reader(handle, delimiter="\t")
            for row in reader:
                if not row:
                    continue
                if len(row) >= 6:
                    label = row[4]
                    surface = row[-1].strip()
                elif len(row) >= 2:
                    label = row[0]
                    surface = row[-1].strip()
                else:
                    continue
                if not surface or not _is_person_label(label):
                    continue
                start, end = _search_span(chunk.text, surface, search_cursor)
                if start < 0:
                    continue
                search_cursor = end
                mentions.append(
                    MentionRecord(
                        mention_id=build_mention_id(chunk.chunk_id, len(mentions) + 1),
                        chunk_id=chunk.chunk_id,
                        surface_form=surface,
                        normalized_form=surface.lower(),
                        entity_type="person",
                        speaker_hint=quote_hints.get(surface.lower(), ""),
                        span_start=start,
                        span_end=end,
                    )
                )
        return mentions


def _guess_speaker_hint(text: str, start: int) -> str:
    prefix = text[max(0, start - 40):start]
    if '"' in prefix or "'" in prefix:
        return "quoted_context"
    return ""


def _load_quote_hints(quotes_path: Path) -> dict[str, str]:
    if not quotes_path.exists():
        return {}
    hints: dict[str, str] = {}
    with quotes_path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if not row:
                continue
            surface = row[-1].strip().lower()
            if surface:
                hints[surface] = "quoted_context"
    return hints


def _search_span(text: str, surface: str, cursor: int) -> tuple[int, int]:
    start = text.find(surface, cursor)
    if start < 0:
        start = text.find(surface)
    if start < 0:
        return (-1, -1)
    return (start, start + len(surface))


def _is_person_label(label: str) -> bool:
    normalized = label.lower()
    return normalized in {"per", "person", "proper"} or "per" in normalized or "person" in normalized
