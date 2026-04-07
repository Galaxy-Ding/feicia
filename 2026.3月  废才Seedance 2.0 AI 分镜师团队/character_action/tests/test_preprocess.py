from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from character_action.models import ChunkRecord
from character_action.preprocess import BookNLPAdapter, HanLPAdapter, normalize_text, route_adapter


class PreprocessTest(unittest.TestCase):
    def test_normalize_text_has_three_random_spacing_cases(self) -> None:
        rng = random.Random(1201)
        for _ in range(3):
            spaces = " " * rng.randint(2, 5)
            text = f"Alice{spaces}Rowan\nMarcus\tVale"
            self.assertEqual(normalize_text(text), "Alice Rowan Marcus Vale")

    def test_route_adapter_has_three_language_cases(self) -> None:
        languages = {"zh": HanLPAdapter, "en": BookNLPAdapter}
        for language, expected in languages.items():
            self.assertIsInstance(route_adapter(language, engine_mode="fallback"), expected)
        with self.assertRaises(ValueError):
            route_adapter("jp")

    def test_hanlp_adapter_normalize_chunk_has_three_random_cases(self) -> None:
        adapter = HanLPAdapter()
        rng = random.Random(1202)
        for _ in range(3):
            name = random.choice(["林晚", "顾昭", "守门内侍"])
            chunk = ChunkRecord(
                chunk_id="ch_0001_ck_0001",
                chapter_id="ch_0001",
                chunk_index=1,
                text=f"{name}看向林晚。顾昭又叫住{name}。",
                char_start=rng.randint(0, 40),
                char_end=200,
            )
            unit = adapter.normalize_chunk("book_demo", "ch_0001", chunk, 16)
            self.assertGreaterEqual(len(unit.mentions), 2)
            self.assertEqual(len(unit.mentions), len(unit.evidences))
            self.assertEqual(unit.language, "zh")

    def test_hanlp_adapter_extracts_title_person_mentions_in_fallback(self) -> None:
        adapter = HanLPAdapter(engine_mode="fallback")
        chunk = ChunkRecord(
            chunk_id="ch_0001_ck_0001",
            chapter_id="ch_0001",
            chunk_index=1,
            text="守门内侍低声提醒林晚，师父已经等了很久。",
            char_start=0,
            char_end=22,
        )
        unit = adapter.normalize_chunk("book_demo", "ch_0001", chunk, 12)
        self.assertEqual([item.surface_form for item in unit.mentions], ["守门内侍", "林晚", "师父"])

    def test_booknlp_adapter_normalize_chunk_has_three_random_cases(self) -> None:
        adapter = BookNLPAdapter()
        names = ["Alice Rowan", "Marcus Vale", "Captain Nora"]
        for index, name in enumerate(names, start=1):
            chunk = ChunkRecord(
                chunk_id="ch_0001_ck_0001",
                chapter_id="ch_0001",
                chunk_index=1,
                text=f'"{name}," Marcus Vale said. Captain Nora answered {name}.',
                char_start=index * 10,
                char_end=160,
            )
            unit = adapter.normalize_chunk("book_demo", "ch_0001", chunk, 20)
            self.assertGreaterEqual(len(unit.mentions), 2)
            self.assertEqual(len(unit.mentions), len(unit.evidences))
            self.assertEqual(unit.language, "en")

    def test_hanlp_native_adapter_mock_case(self) -> None:
        fake_hanlp = ModuleType("hanlp")
        fake_hanlp.pretrained = SimpleNamespace(
            mtl=SimpleNamespace(TEST_ZH_MODEL="dummy"),
            ner=SimpleNamespace(TEST_ZH_MODEL="dummy"),
        )
        fake_hanlp.load = lambda _model: (
            lambda _text: {"tok": ["林晚", "看见", "顾昭"], "ner": [("林晚", "PER", 0, 1), ("顾昭", "PER", 2, 3)]}
        )
        chunk = ChunkRecord(
            chunk_id="ch_0001_ck_0001",
            chapter_id="ch_0001",
            chunk_index=1,
            text="林晚看见顾昭",
            char_start=0,
            char_end=6,
        )
        with patch.dict(sys.modules, {"hanlp": fake_hanlp}):
            unit = HanLPAdapter(engine_mode="native", model_name="TEST_ZH_MODEL").normalize_chunk("book_demo", "ch_0001", chunk, 8)
        self.assertEqual(unit.adapter_name, "hanlp_native:TEST_ZH_MODEL")
        self.assertEqual([item.surface_form for item in unit.mentions], ["林晚", "顾昭"])

    def test_hanlp_native_adapter_adds_title_person_mentions_when_ner_misses_them(self) -> None:
        fake_hanlp = ModuleType("hanlp")
        fake_hanlp.pretrained = SimpleNamespace(
            mtl=SimpleNamespace(TEST_ZH_MODEL="dummy"),
            ner=SimpleNamespace(TEST_ZH_MODEL="dummy"),
        )
        fake_hanlp.load = lambda _model: (
            lambda _text: {
                "tok": ["守门", "内侍", "提醒", "林晚", "，", "师父", "已经", "等了", "很久", "。"],
                "ner": [("林晚", "PER", 3, 4)],
            }
        )
        chunk = ChunkRecord(
            chunk_id="ch_0001_ck_0001",
            chapter_id="ch_0001",
            chunk_index=1,
            text="守门内侍提醒林晚，师父已经等了很久。",
            char_start=0,
            char_end=18,
        )
        with patch.dict(sys.modules, {"hanlp": fake_hanlp}):
            unit = HanLPAdapter(engine_mode="native", model_name="TEST_ZH_MODEL").normalize_chunk("book_demo", "ch_0001", chunk, 8)
        self.assertEqual(unit.adapter_name, "hanlp_native:TEST_ZH_MODEL")
        self.assertEqual([item.surface_form for item in unit.mentions], ["林晚", "守门内侍", "师父"])

    def test_booknlp_native_adapter_mock_case(self) -> None:
        fake_pkg = ModuleType("booknlp")
        fake_mod = ModuleType("booknlp.booknlp")

        class FakeBookNLP:
            def __init__(self, _language, _params):
                pass

            def process(self, _input_path, output_dir, file_id):
                output = Path(output_dir)
                output.mkdir(parents=True, exist_ok=True)
                (output / f"{file_id}.entities").write_text(
                    "0\t0\t0\t1\tPER\tAlice Rowan\n1\t0\t2\t3\tPER\tMarcus Vale\n",
                    encoding="utf-8",
                )
                (output / f"{file_id}.quotes").write_text(
                    "0\t0\t0\t0\tAlice Rowan\n",
                    encoding="utf-8",
                )

        fake_mod.BookNLP = FakeBookNLP
        chunk = ChunkRecord(
            chunk_id="ch_0001_ck_0001",
            chapter_id="ch_0001",
            chunk_index=1,
            text='Alice Rowan met Marcus Vale. "Alice Rowan" said hello.',
            char_start=0,
            char_end=56,
        )
        with patch.dict(sys.modules, {"booknlp": fake_pkg, "booknlp.booknlp": fake_mod}):
            unit = BookNLPAdapter(engine_mode="native", native_temp_root=None).normalize_chunk("book_demo", "ch_0001", chunk, 12)
        self.assertEqual(unit.adapter_name, "booknlp_native:small")
        self.assertGreaterEqual(len(unit.mentions), 2)


if __name__ == "__main__":
    unittest.main()
