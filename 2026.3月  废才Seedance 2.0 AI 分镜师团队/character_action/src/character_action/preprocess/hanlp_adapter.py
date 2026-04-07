from __future__ import annotations

import importlib
import re
from typing import Any

from ..evidence import build_evidence_for_mention
from ..ids import build_mention_id
from ..models import ChunkRecord, MentionRecord, NormalizedTextUnit
from .text_utils import normalize_text

_NAME_RE = re.compile(
    r"(?:"
    r"(?:欧阳|司马|上官|诸葛|东方|独孤|南宫|令狐|皇甫|慕容|尉迟|长孙|宇文|司徒|夏侯|轩辕|司空|端木|百里|呼延|拓跋|公孙|闻人|澹台)[\u4e00-\u9fff]{1,2}"
    r"|"
    r"[赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季强贾路娄危江童颜郭梅盛林钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪解应宗丁宣邓郁单杭洪包左石崔吉龚程嵇邢滑裴陆荣翁荀羊甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴鬱胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎连习容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东殴沃利蔚越夔隆师巩厍聂晁勾敖融冷辛阚简饶曾沙养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公][\u4e00-\u9fff]"
    r")"
)
_SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
_TITLE_PERSON_RE = re.compile(
    r"(?:"
    r"[\u4e00-\u9fff]{0,2}(?:内侍|侍卫|护卫|门房|管家|嬷嬷|掌柜|郎中|大夫)"
    r"|"
    r"师父|师傅|老师|先生|夫人|小姐|公子|少爷|姑娘|丫鬟|仆人|陛下|殿下|道长|住持|方丈|师兄|师姐|师弟|师妹"
    r")"
)
_STOPWORDS = {
    "我们",
    "你们",
    "他们",
    "她们",
    "一个",
    "两个",
    "现在",
    "这里",
    "那里",
    "不是",
    "没有",
    "如果",
    "但是",
    "先生们",
    "小姐们",
}
_NAME_INVALID_CHARS = set("的了在是也已和与及并说看着将把向对到又很太都而让等去来上下中前后里外这那谁何么呢啊呀吧吗")


class HanLPAdapter:
    def __init__(self, *, engine_mode: str = "auto", model_name: str | None = None) -> None:
        self.engine_mode = engine_mode
        self.model_name = model_name or "OPEN_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH"
        self.adapter_name = "hanlp_fallback"
        self._native = None

    def normalize_chunk(self, book_id: str, chapter_id: str, chunk: ChunkRecord, evidence_window: int) -> NormalizedTextUnit:
        if self.engine_mode != "fallback":
            try:
                native = self._load_native()
                if native is not None:
                    return self._normalize_chunk_native(book_id, chapter_id, chunk, evidence_window, native)
            except Exception:
                if self.engine_mode == "native":
                    raise
        mentions: list[MentionRecord] = []
        evidences = []
        seen_spans: set[tuple[int, int]] = set()
        for match in _iter_fallback_person_matches(chunk.text):
            surface = match.group(0)
            if surface in _STOPWORDS:
                continue
            span = (match.start(), match.end())
            if span in seen_spans:
                continue
            _append_mention(
                book_id=book_id,
                chapter_id=chapter_id,
                chunk=chunk,
                mentions=mentions,
                evidences=evidences,
                seen_spans=seen_spans,
                surface=surface,
                span_start=match.start(),
                span_end=match.end(),
                evidence_window=evidence_window,
            )
        return NormalizedTextUnit(
            book_id=book_id,
            chapter_id=chapter_id,
            chunk=chunk,
            language="zh",
            sentences=[normalize_text(item.group(0)) for item in _SENTENCE_RE.finditer(chunk.text) if normalize_text(item.group(0))],
            mentions=mentions,
            evidences=evidences,
            adapter_name=self.adapter_name,
        )

    def _load_native(self):
        if self._native is not None:
            return self._native
        hanlp = importlib.import_module("hanlp")
        pretrained = getattr(hanlp, "pretrained", None)
        candidates: list[Any] = [self.model_name]
        if pretrained is not None:
            for group_name in ("mtl", "ner"):
                group = getattr(pretrained, group_name, None)
                if group is not None and hasattr(group, self.model_name):
                    candidates.insert(0, getattr(group, self.model_name))
        last_error = None
        for candidate in candidates:
            try:
                self._native = hanlp.load(candidate)
                return self._native
            except Exception as exc:  # pragma: no cover - depends on external runtime
                last_error = exc
        if last_error is not None:
            raise last_error
        return None

    def _normalize_chunk_native(
        self,
        book_id: str,
        chapter_id: str,
        chunk: ChunkRecord,
        evidence_window: int,
        native,
    ) -> NormalizedTextUnit:
        result = native(chunk.text)
        tokens = _extract_hanlp_tokens(result)
        entities = _extract_hanlp_entities(result)
        if not tokens:
            raise RuntimeError("HanLP native output missing tokens")
        token_offsets = _align_tokens_to_text(chunk.text, tokens)
        mentions: list[MentionRecord] = []
        evidences = []
        seen_spans: set[tuple[int, int]] = set()
        for entity in entities:
            surface, label, start_token, end_token = entity
            if not _is_person_label(label):
                continue
            if start_token < 0 or end_token <= start_token or end_token > len(token_offsets):
                continue
            span_start = token_offsets[start_token][0]
            span_end = token_offsets[end_token - 1][1]
            _append_mention(
                book_id=book_id,
                chapter_id=chapter_id,
                chunk=chunk,
                mentions=mentions,
                evidences=evidences,
                seen_spans=seen_spans,
                surface=surface,
                span_start=span_start,
                span_end=span_end,
                evidence_window=evidence_window,
            )
        for match in _iter_title_person_matches(chunk.text):
            _append_mention(
                book_id=book_id,
                chapter_id=chapter_id,
                chunk=chunk,
                mentions=mentions,
                evidences=evidences,
                seen_spans=seen_spans,
                surface=match.group(0),
                span_start=match.start(),
                span_end=match.end(),
                evidence_window=evidence_window,
            )
        if not mentions:
            raise RuntimeError("HanLP native output did not yield person mentions")
        self.adapter_name = f"hanlp_native:{self.model_name}"
        return NormalizedTextUnit(
            book_id=book_id,
            chapter_id=chapter_id,
            chunk=chunk,
            language="zh",
            sentences=[normalize_text(item.group(0)) for item in _SENTENCE_RE.finditer(chunk.text) if normalize_text(item.group(0))],
            mentions=mentions,
            evidences=evidences,
            adapter_name=self.adapter_name,
        )


def _extract_hanlp_tokens(result: Any) -> list[str]:
    if isinstance(result, dict):
        for key in ("tok/fine", "tok/coarse", "tok"):
            tokens = result.get(key)
            if isinstance(tokens, list):
                if tokens and isinstance(tokens[0], list):
                    return list(tokens[0])
                if all(isinstance(item, str) for item in tokens):
                    return list(tokens)
    if hasattr(result, "get"):
        for key in ("tok/fine", "tok/coarse", "tok"):
            try:
                tokens = result.get(key)
            except Exception:
                tokens = None
            if isinstance(tokens, list):
                if tokens and isinstance(tokens[0], list):
                    return list(tokens[0])
                if all(isinstance(item, str) for item in tokens):
                    return list(tokens)
    return []


def _extract_hanlp_entities(result: Any) -> list[tuple[str, str, int, int]]:
    sequences = _find_hanlp_entity_sequences(result)
    entities: list[tuple[str, str, int, int]] = []
    for sequence in sequences:
        for item in sequence:
            if isinstance(item, (list, tuple)) and len(item) >= 4:
                surface = str(item[0])
                label = str(item[1])
                start = int(item[2])
                end = int(item[3])
                entities.append((surface, label, start, end))
    return entities


def _find_hanlp_entity_sequences(result: Any) -> list[list[Any]]:
    sequences: list[list[Any]] = []
    if isinstance(result, dict):
        for key, value in result.items():
            if "ner" in str(key).lower():
                if isinstance(value, list) and value and isinstance(value[0], (list, tuple)):
                    if isinstance(value[0], (list, tuple)) and len(value[0]) >= 4:
                        sequences.append(list(value))
                    else:
                        for child in value:
                            if isinstance(child, list):
                                sequences.append(child)
    if hasattr(result, "items") and not isinstance(result, dict):
        try:
            for key, value in result.items():
                if "ner" in str(key).lower():
                    if isinstance(value, list) and value and isinstance(value[0], (list, tuple)):
                        if len(value[0]) >= 4:
                            sequences.append(list(value))
                        else:
                            for child in value:
                                if isinstance(child, list):
                                    sequences.append(child)
        except Exception:
            pass
    return sequences


def _align_tokens_to_text(text: str, tokens: list[str]) -> list[tuple[int, int]]:
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for token in tokens:
        start = text.find(token, cursor)
        if start < 0:
            start = text.find(token)
        if start < 0:
            raise RuntimeError(f"Unable to align HanLP token {token!r}")
        end = start + len(token)
        offsets.append((start, end))
        cursor = end
    return offsets


def _is_person_label(label: str) -> bool:
    normalized = label.lower()
    return normalized in {"nr", "per", "person"} or "person" in normalized or normalized.endswith("per")


def _iter_fallback_person_matches(text: str):
    collected: list[tuple[int, int, Any]] = []
    seen_spans: set[tuple[int, int]] = set()
    for match in _TITLE_PERSON_RE.finditer(text):
        span = (match.start(), match.end())
        if match.group(0) in _STOPWORDS or span in seen_spans:
            continue
        seen_spans.add(span)
        collected.append((match.start(), match.end(), match))
    for match in _NAME_RE.finditer(text):
        surface = match.group(0)
        span = (match.start(), match.end())
        if surface in _STOPWORDS or span in seen_spans or not _looks_like_chinese_name(surface):
            continue
        if any(_spans_overlap(span, existing_span) for existing_span in seen_spans):
            continue
        seen_spans.add(span)
        collected.append((match.start(), match.end(), match))
    for _start, _end, match in sorted(collected, key=lambda item: (item[0], item[1])):
        yield match


def _iter_title_person_matches(text: str):
    for match in _TITLE_PERSON_RE.finditer(text):
        if match.group(0) in _STOPWORDS:
            continue
        yield match


def _looks_like_chinese_name(surface: str) -> bool:
    if len(surface) < 2 or len(surface) > 4:
        return False
    body = surface[2:] if surface[:2] in {"欧阳", "司马", "上官", "诸葛", "东方", "独孤", "南宫", "令狐", "皇甫", "慕容", "尉迟", "长孙", "宇文", "司徒", "夏侯", "轩辕", "司空", "端木", "百里", "呼延", "拓跋", "公孙", "闻人", "澹台"} else surface[1:]
    return bool(body) and not any(char in _NAME_INVALID_CHARS for char in body)


def _spans_overlap(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def _append_mention(
    *,
    book_id: str,
    chapter_id: str,
    chunk: ChunkRecord,
    mentions: list[MentionRecord],
    evidences: list[Any],
    seen_spans: set[tuple[int, int]],
    surface: str,
    span_start: int,
    span_end: int,
    evidence_window: int,
) -> None:
    span = (span_start, span_end)
    if not surface or span in seen_spans:
        return
    seen_spans.add(span)
    mention = MentionRecord(
        mention_id=build_mention_id(chunk.chunk_id, len(mentions) + 1),
        chunk_id=chunk.chunk_id,
        surface_form=surface,
        normalized_form=surface,
        entity_type="person",
        speaker_hint="",
        span_start=span_start,
        span_end=span_end,
    )
    mentions.append(mention)
    evidences.append(build_evidence_for_mention(book_id, chapter_id, chunk, mention, len(evidences) + 1, evidence_window))
