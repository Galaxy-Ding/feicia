from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from character_action.pipeline import CharacterActionPipeline


class PipelineTest(unittest.TestCase):
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

    def test_pipeline_preprocess_book_functional_for_zh_and_en(self) -> None:
        fixtures = {
            "zh": ("book_demo_zh", "中文样书", Path(__file__).resolve().parent / "fixtures" / "books" / "demo_zh.txt"),
            "en": ("book_demo_en", "English Demo", Path(__file__).resolve().parent / "fixtures" / "books" / "demo_en.txt"),
        }
        for language, (book_id, title, fixture) in fixtures.items():
            with tempfile.TemporaryDirectory() as tmp:
                root = self._build_project(tmp)
                target = root / "data" / "raw_books" / fixture.name
                shutil.copy(fixture, target)
                payload = CharacterActionPipeline(root).preprocess_book(
                    book_id=book_id,
                    title=title,
                    language=language,
                    input_path=target.relative_to(root),
                )
                self.assertGreaterEqual(payload["chapter_count"], 1)
                self.assertGreaterEqual(payload["chunk_count"], 1)
                self.assertGreaterEqual(payload["mention_count"], 1)
                export_path = Path(payload["normalized_path"])
                self.assertTrue(export_path.exists())
                extract = CharacterActionPipeline(root).extract_characters(book_id=book_id)
                self.assertGreaterEqual(extract["character_count"], 1)
                self.assertTrue(Path(extract["characters_path"]).exists())
                relations = CharacterActionPipeline(root).build_relations(book_id=book_id)
                self.assertGreaterEqual(relations["relation_count"], 1)
                self.assertTrue(Path(relations["relation_graph_path"]).exists())
                qa_result = CharacterActionPipeline(root).run_qa(book_id=book_id)
                self.assertGreaterEqual(qa_result["qa_finding_count"], 0)
                self.assertTrue(Path(qa_result["qa_findings_path"]).exists())

    def test_cli_prepare_and_status_integration(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = self._build_project(tmp)
            env = os.environ.copy()
            env["PYTHONPATH"] = str(package_root / "src")
            prepare = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "prepare",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            prepare_payload = json.loads(prepare.stdout)
            self.assertTrue(Path(prepare_payload["sqlite_path"]).exists())
            status = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "status",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            status_payload = json.loads(status.stdout)
            self.assertIn("books", status_payload)

    def test_cli_doctor_and_extract_integration(self) -> None:
        package_root = Path(__file__).resolve().parents[1]
        fixture = Path(__file__).resolve().parent / "fixtures" / "books" / "demo_en.txt"
        with tempfile.TemporaryDirectory() as tmp:
            root = self._build_project(tmp)
            shutil.copy(fixture, root / "data" / "raw_books" / "demo_en.txt")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(package_root / "src")
            doctor = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "doctor",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            doctor_payload = json.loads(doctor.stdout)
            self.assertIn("hanlp", doctor_payload)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "preprocess-book",
                    "--book-id",
                    "demo_en",
                    "--title",
                    "English Demo",
                    "--language",
                    "en",
                    "--input",
                    "data/raw_books/demo_en.txt",
                    "--engine-mode",
                    "fallback",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            extract = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "extract-characters",
                    "--book-id",
                    "demo_en",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            extract_payload = json.loads(extract.stdout)
            self.assertGreaterEqual(extract_payload["character_count"], 1)
            self.assertTrue(Path(extract_payload["review_queue_path"]).exists())
            relations = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "build-relations",
                    "--book-id",
                    "demo_en",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            relation_payload = json.loads(relations.stdout)
            self.assertGreaterEqual(relation_payload["relation_count"], 1)
            qa = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "run-qa",
                    "--book-id",
                    "demo_en",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            qa_payload = json.loads(qa.stdout)
            self.assertGreaterEqual(qa_payload["qa_finding_count"], 1)
            status = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "character_action.cli",
                    "--project-root",
                    str(root),
                    "status",
                    "--book-id",
                    "demo_en",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            status_payload = json.loads(status.stdout)
            self.assertGreaterEqual(status_payload["relation_count"], 1)
            self.assertGreaterEqual(status_payload["qa_finding_count"], 1)


if __name__ == "__main__":
    unittest.main()
