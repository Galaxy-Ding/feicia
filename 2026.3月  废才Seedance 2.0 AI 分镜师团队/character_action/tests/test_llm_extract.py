from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from character_action.pipeline import CharacterActionPipeline


class MockDualLLMClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def chat(self, model, messages: list[dict[str, str]]) -> str:
        prompt = messages[-1]["content"]
        self.calls.append({"provider": model.provider, "model": model.name, "prompt": prompt})
        payload = json.loads(prompt)
        if model.provider == "codex":
            if payload["chunk_id"] == "ch_0001_ck_0001":
                return json.dumps(
                    {
                        "characters": [
                            {"canonical_name": "顾星澜", "aliases": ["顾女官", "星澜"], "roles": ["person"], "evidence_surfaces": ["顾星澜", "顾女官", "星澜"], "confidence": 0.91},
                            {"canonical_name": "守门内侍", "aliases": ["内侍", "公公", "老奴"], "roles": ["guard", "attendant"], "evidence_surfaces": ["守门内侍", "内侍", "公公", "老奴"], "confidence": 0.86},
                        ]
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {
                    "characters": [
                        {"canonical_name": "沈钧", "aliases": ["师傅"], "roles": ["mentor"], "evidence_surfaces": ["沈钧", "师傅"], "confidence": 0.55},
                        {"canonical_name": "顾星澜", "aliases": ["顾女官"], "roles": ["person"], "evidence_surfaces": ["顾星澜", "顾女官"], "confidence": 0.82},
                    ]
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "characters": [
                    {
                        "canonical_name": "顾星澜",
                        "aliases": ["星澜", "顾女官"],
                        "roles": ["person"],
                        "evidence_surfaces": ["顾星澜", "顾女官", "星澜"],
                        "summary": "宫中女官角色。",
                        "confidence": 0.92,
                    },
                    {
                        "canonical_name": "守门内侍",
                        "aliases": ["内侍", "公公", "老奴"],
                        "roles": ["guard", "attendant", "person"],
                        "evidence_surfaces": ["守门内侍", "内侍", "公公", "老奴"],
                        "summary": "宫门值守内侍。",
                        "confidence": 0.88,
                    },
                    {
                        "canonical_name": "沈钧",
                        "aliases": ["师傅"],
                        "roles": ["mentor", "person"],
                        "evidence_surfaces": ["沈钧", "师傅"],
                        "summary": "主角师门长辈。",
                        "confidence": 0.55,
                    },
                ]
            },
            ensure_ascii=False,
        )


class LLMExtractPipelineTest(unittest.TestCase):
    def _build_project(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "configs").mkdir()
        (root / "data" / "raw_books").mkdir(parents=True)
        (root / "data" / "normalized").mkdir(parents=True)
        (root / "data" / "exports").mkdir(parents=True)
        (root / "logs").mkdir()
        (root / "schemas").mkdir()
        source = Path(__file__).resolve().parents[1]
        shutil.copy(source / "configs" / "dev.yaml", root / "configs" / "dev.yaml")
        for schema in (source / "schemas").glob("*.json"):
            shutil.copy(schema, root / "schemas" / schema.name)
        return root

    def test_extract_characters_llm_runs_dual_model_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._build_project(tmp)
            normalized = {
                "run_id": "book_demo-20260328070000",
                "book": {
                    "book_id": "book_demo",
                    "title": "Demo",
                    "language": "zh",
                    "author": "",
                    "source_path": "data/raw_books/demo.txt",
                    "chapter_count": 2,
                },
                "normalized_units": [
                    {
                        "book_id": "book_demo",
                        "chapter_id": "ch_0001",
                        "chunk": {
                            "chunk_id": "ch_0001_ck_0001",
                            "chapter_id": "ch_0001",
                            "chunk_index": 1,
                            "text": "顾星澜向守门内侍使了个眼色，顾女官低声让公公开门。",
                            "char_start": 0,
                            "char_end": 28,
                        },
                        "language": "zh",
                        "sentences": ["顾星澜向守门内侍使了个眼色，顾女官低声让公公开门。"],
                        "mentions": [
                            {"mention_id": "ch_0001_ck_0001_mn_0001", "chunk_id": "ch_0001_ck_0001", "surface_form": "顾星澜", "normalized_form": "顾星澜", "entity_type": "person", "speaker_hint": "", "span_start": 0, "span_end": 3},
                            {"mention_id": "ch_0001_ck_0001_mn_0002", "chunk_id": "ch_0001_ck_0001", "surface_form": "守门内侍", "normalized_form": "守门内侍", "entity_type": "person", "speaker_hint": "", "span_start": 4, "span_end": 8},
                            {"mention_id": "ch_0001_ck_0001_mn_0003", "chunk_id": "ch_0001_ck_0001", "surface_form": "顾女官", "normalized_form": "顾女官", "entity_type": "person", "speaker_hint": "", "span_start": 13, "span_end": 16},
                            {"mention_id": "ch_0001_ck_0001_mn_0004", "chunk_id": "ch_0001_ck_0001", "surface_form": "公公", "normalized_form": "公公", "entity_type": "person", "speaker_hint": "", "span_start": 21, "span_end": 23},
                        ],
                        "evidences": [
                            {"evidence_id": "ch_0001_ck_0001_ev_0001", "book_id": "book_demo", "chapter_id": "ch_0001", "chunk_id": "ch_0001_ck_0001", "quote_text": "顾星澜向守门内侍使了个眼色", "span_start": 0, "span_end": 3, "linked_object_type": "mention", "linked_object_id": "ch_0001_ck_0001_mn_0001"},
                            {"evidence_id": "ch_0001_ck_0001_ev_0002", "book_id": "book_demo", "chapter_id": "ch_0001", "chunk_id": "ch_0001_ck_0001", "quote_text": "顾星澜向守门内侍使了个眼色", "span_start": 4, "span_end": 8, "linked_object_type": "mention", "linked_object_id": "ch_0001_ck_0001_mn_0002"},
                            {"evidence_id": "ch_0001_ck_0001_ev_0003", "book_id": "book_demo", "chapter_id": "ch_0001", "chunk_id": "ch_0001_ck_0001", "quote_text": "顾女官低声让公公开门", "span_start": 13, "span_end": 16, "linked_object_type": "mention", "linked_object_id": "ch_0001_ck_0001_mn_0003"},
                            {"evidence_id": "ch_0001_ck_0001_ev_0004", "book_id": "book_demo", "chapter_id": "ch_0001", "chunk_id": "ch_0001_ck_0001", "quote_text": "顾女官低声让公公开门", "span_start": 21, "span_end": 23, "linked_object_type": "mention", "linked_object_id": "ch_0001_ck_0001_mn_0004"},
                        ],
                        "adapter_name": "test",
                    },
                    {
                        "book_id": "book_demo",
                        "chapter_id": "ch_0002",
                        "chunk": {
                            "chunk_id": "ch_0002_ck_0001",
                            "chapter_id": "ch_0002",
                            "chunk_index": 1,
                            "text": "沈钧听见星澜叫他师傅，老奴在一旁点头。",
                            "char_start": 0,
                            "char_end": 22,
                        },
                        "language": "zh",
                        "sentences": ["沈钧听见星澜叫他师傅，老奴在一旁点头。"],
                        "mentions": [
                            {"mention_id": "ch_0002_ck_0001_mn_0001", "chunk_id": "ch_0002_ck_0001", "surface_form": "沈钧", "normalized_form": "沈钧", "entity_type": "person", "speaker_hint": "", "span_start": 0, "span_end": 2},
                            {"mention_id": "ch_0002_ck_0001_mn_0002", "chunk_id": "ch_0002_ck_0001", "surface_form": "星澜", "normalized_form": "星澜", "entity_type": "person", "speaker_hint": "", "span_start": 4, "span_end": 6},
                            {"mention_id": "ch_0002_ck_0001_mn_0003", "chunk_id": "ch_0002_ck_0001", "surface_form": "师傅", "normalized_form": "师傅", "entity_type": "person", "speaker_hint": "", "span_start": 8, "span_end": 10},
                            {"mention_id": "ch_0002_ck_0001_mn_0004", "chunk_id": "ch_0002_ck_0001", "surface_form": "老奴", "normalized_form": "老奴", "entity_type": "person", "speaker_hint": "", "span_start": 11, "span_end": 13},
                        ],
                        "evidences": [
                            {"evidence_id": "ch_0002_ck_0001_ev_0001", "book_id": "book_demo", "chapter_id": "ch_0002", "chunk_id": "ch_0002_ck_0001", "quote_text": "沈钧听见星澜叫他师傅", "span_start": 0, "span_end": 2, "linked_object_type": "mention", "linked_object_id": "ch_0002_ck_0001_mn_0001"},
                            {"evidence_id": "ch_0002_ck_0001_ev_0002", "book_id": "book_demo", "chapter_id": "ch_0002", "chunk_id": "ch_0002_ck_0001", "quote_text": "沈钧听见星澜叫他师傅", "span_start": 4, "span_end": 6, "linked_object_type": "mention", "linked_object_id": "ch_0002_ck_0001_mn_0002"},
                            {"evidence_id": "ch_0002_ck_0001_ev_0003", "book_id": "book_demo", "chapter_id": "ch_0002", "chunk_id": "ch_0002_ck_0001", "quote_text": "沈钧听见星澜叫他师傅", "span_start": 8, "span_end": 10, "linked_object_type": "mention", "linked_object_id": "ch_0002_ck_0001_mn_0003"},
                            {"evidence_id": "ch_0002_ck_0001_ev_0004", "book_id": "book_demo", "chapter_id": "ch_0002", "chunk_id": "ch_0002_ck_0001", "quote_text": "老奴在一旁点头", "span_start": 11, "span_end": 13, "linked_object_type": "mention", "linked_object_id": "ch_0002_ck_0001_mn_0004"},
                        ],
                        "adapter_name": "test",
                    },
                ],
            }
            normalized_path = root / "data" / "normalized" / "book_demo.json"
            normalized_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")

            pipeline = CharacterActionPipeline(root, llm_client=MockDualLLMClient())
            payload = pipeline.extract_characters_llm(book_id="book_demo")

            self.assertEqual(payload["character_count"], 3)
            self.assertTrue(Path(payload["characters_path"]).exists())
            self.assertTrue(Path(payload["review_queue_path"]).exists())
            self.assertTrue(Path(payload["llm_character_candidates_path"]).exists())
            self.assertTrue(Path(payload["llm_character_review_path"]).exists())

            character_payload = json.loads(Path(payload["characters_path"]).read_text(encoding="utf-8"))
            names = {item["canonical_name"]: item for item in character_payload["characters"]}
            self.assertEqual(set(names), {"顾星澜", "守门内侍", "沈钧"})
            self.assertEqual(sorted(names["顾星澜"]["aliases"]), ["星澜", "顾女官"])
            self.assertEqual(sorted(names["守门内侍"]["aliases"]), ["公公", "内侍", "老奴"])
            self.assertEqual(sorted(names["沈钧"]["aliases"]), ["师傅"])

            review_payload = json.loads(Path(payload["review_queue_path"]).read_text(encoding="utf-8"))
            self.assertEqual(len(review_payload["tasks"]), 1)
            self.assertEqual(review_payload["tasks"][0]["task_type"], "low_confidence_character")


if __name__ == "__main__":
    unittest.main()
