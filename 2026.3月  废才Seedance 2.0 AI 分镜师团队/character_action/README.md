# Character Action

`character_action/` is the standalone upstream novel character extraction project.

Position in the workspace:

- `character_action`: novel text ingestion, chunking, normalized mentions, evidence spans, SQLite persistence
- `video_only_once_phase1`: unified bridge and future scheduler
- `fenjing_program`: downstream storyboard and character asset consumer

Phase 02 scope implemented here:

- project config and runtime preparation
- chapter split and chunk rules
- normalized text unit contracts
- fallback `HanLP` and `BookNLP` style adapters
- SQLite persistence and run audit log

Phase 03 additions:

- native-or-fallback adapter routing
- `doctor` runtime dependency check
- alias merge and `character_cards.json`
- review queue generation and SQLite persistence
- `video_only_once_phase1` bridge readiness

Commands:

```bash
PYTHONPATH=src python3 -m character_action.cli prepare --project-root .
PYTHONPATH=src python3 -m character_action.cli doctor --project-root .
PYTHONPATH=src python3 -m character_action.cli preprocess-book --project-root . --book-id book_demo --title "Demo" --language zh --input data/raw_books/demo_zh.txt
PYTHONPATH=src python3 -m character_action.cli extract-characters --project-root . --book-id book_demo
PYTHONPATH=src python3 -m character_action.cli extract-characters-llm --project-root . --book-id book_demo --llm-config ../fenjing_program/project-config.local.json
PYTHONPATH=src python3 -m character_action.cli build-relations --project-root . --book-id book_demo
PYTHONPATH=src python3 -m character_action.cli run-qa --project-root . --book-id book_demo
PYTHONPATH=src python3 -m character_action.cli status --project-root . --book-id book_demo
```

Testing:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Native runtime install:

```bash
python3 -m pip install --user virtualenv
cd character_action
~/.local/bin/virtualenv .venv
./.venv/bin/pip install -e . -r requirements-native.txt
```

`BookNLP` needs `en_core_web_sm`. If GitHub is reachable:

```bash
./.venv/bin/python -m spacy download en_core_web_sm
```

If GitHub is blocked, install the same model from `conda-forge`:

```bash
curl -L -o /tmp/en_core_web_sm.conda \
  https://conda.anaconda.org/conda-forge/noarch/spacy-model-en_core_web_sm-3.8.0-pyhd8ed1ab_0.conda
./.venv/bin/python - <<'PY'
import pathlib
import tarfile
import zipfile

import zstandard

conda_path = pathlib.Path("/tmp/en_core_web_sm.conda")
site_packages = pathlib.Path(".venv/lib/python3.10/site-packages").resolve()
with zipfile.ZipFile(conda_path) as zf:
    pkg_name = next(name for name in zf.namelist() if name.startswith("pkg-"))
    tar_bytes = zstandard.ZstdDecompressor().decompress(zf.read(pkg_name))
tar_path = pathlib.Path("/tmp/en_core_web_sm.tar")
tar_path.write_bytes(tar_bytes)
with tarfile.open(tar_path) as tf:
    for member in tf.getmembers():
        if not member.name.startswith("site-packages/"):
            continue
        rel = pathlib.Path(member.name).relative_to("site-packages")
        target = site_packages / rel
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        src = tf.extractfile(member)
        if src is not None:
            target.write_bytes(src.read())
PY
```

Native verification:

```bash
./.venv/bin/python -m character_action.cli --project-root . doctor
./.venv/bin/python -m character_action.cli --project-root . preprocess-book --book-id book_demo_zh_native --title "Demo ZH Native" --language zh --input data/raw_books/demo_zh.txt --engine-mode native
HF_ENDPOINT=https://hf-mirror.com ./.venv/bin/python -m character_action.cli --project-root . preprocess-book --book-id book_demo_en_native --title "Demo EN Native" --language en --input data/raw_books/demo_en.txt --engine-mode native
./.venv/bin/python -m character_action.cli --project-root . extract-characters --book-id book_demo_zh_native
./.venv/bin/python -m character_action.cli --project-root . extract-characters --book-id book_demo_en_native
./.venv/bin/python -m character_action.cli --project-root . build-relations --book-id book_demo_zh_native
./.venv/bin/python -m character_action.cli --project-root . build-relations --book-id book_demo_en_native
./.venv/bin/python -m character_action.cli --project-root . run-qa --book-id book_demo_zh_native
./.venv/bin/python -m character_action.cli --project-root . run-qa --book-id book_demo_en_native
```

Pinned native notes:

- `BookNLP 1.0.8` still imports `pkg_resources`, so `setuptools` must stay below `81`.
- `HanLP 2.1.3` native path fails on `transformers 5.x`; keep `transformers==4.30.2`.
- In this environment, `BookNLP` model downloads need `HF_ENDPOINT=https://hf-mirror.com`.
