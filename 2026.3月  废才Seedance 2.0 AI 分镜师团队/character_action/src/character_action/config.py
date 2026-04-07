from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DataPaths:
    raw_books: Path
    normalized: Path
    exports: Path
    logs: Path


@dataclass(frozen=True)
class RuntimeConfig:
    project_root: Path
    config_path: Path
    data: DataPaths
    sqlite_path: Path
    chunk_size: int
    chunk_overlap: int
    evidence_window: int
    adapter_mode: str
    hanlp_model: str
    booknlp_model: str
    booknlp_pipeline: str
    native_temp_root: Path


def ensure_within_root(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    resolved_candidate.relative_to(resolved_root)
    return resolved_candidate


def load_config(project_root: Path, config_path: str | Path = "configs/dev.yaml") -> RuntimeConfig:
    root = project_root.resolve()
    config_file = ensure_within_root(root, root / config_path if not Path(config_path).is_absolute() else Path(config_path))
    payload = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    data_root = payload.get("data", {})
    runtime_root = payload.get("runtime", {})
    chunk_size = int(runtime_root.get("chunk_size", 280))
    chunk_overlap = int(runtime_root.get("chunk_overlap", 40))
    evidence_window = int(runtime_root.get("evidence_window", 32))
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and < chunk_size")
    if evidence_window <= 0:
        raise ValueError("evidence_window must be > 0")
    adapter_mode = str(runtime_root.get("adapter_mode", "auto")).strip().lower()
    if adapter_mode not in {"auto", "native", "fallback"}:
        raise ValueError("adapter_mode must be one of auto/native/fallback")
    return RuntimeConfig(
        project_root=root,
        config_path=config_file,
        data=DataPaths(
            raw_books=ensure_within_root(root, root / data_root.get("raw_books", "data/raw_books")),
            normalized=ensure_within_root(root, root / data_root.get("normalized", "data/normalized")),
            exports=ensure_within_root(root, root / data_root.get("exports", "data/exports")),
            logs=ensure_within_root(root, root / data_root.get("logs", "logs")),
        ),
        sqlite_path=ensure_within_root(root, root / runtime_root.get("sqlite_path", "data/exports/character_action.sqlite3")),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        evidence_window=evidence_window,
        adapter_mode=adapter_mode,
        hanlp_model=str(runtime_root.get("hanlp_model", "OPEN_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH")),
        booknlp_model=str(runtime_root.get("booknlp_model", "small")),
        booknlp_pipeline=str(runtime_root.get("booknlp_pipeline", "entity,quote")),
        native_temp_root=ensure_within_root(root, root / runtime_root.get("native_temp_root", "data/exports/native_runs")),
    )


def ensure_project_layout(config: RuntimeConfig) -> list[Path]:
    created: list[Path] = []
    for path in (
        config.data.raw_books,
        config.data.normalized,
        config.data.exports,
        config.data.logs,
        config.sqlite_path.parent,
        config.native_temp_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created
