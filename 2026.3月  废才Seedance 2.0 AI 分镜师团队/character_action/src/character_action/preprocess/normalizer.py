from __future__ import annotations


def route_adapter(
    language: str,
    *,
    engine_mode: str = "auto",
    model_name: str | None = None,
    native_temp_root=None,
    pipeline_name: str | None = None,
) -> HanLPAdapter | BookNLPAdapter:
    normalized = language.strip().lower()
    if normalized == "zh":
        from .hanlp_adapter import HanLPAdapter

        return HanLPAdapter(engine_mode=engine_mode, model_name=model_name)
    if normalized == "en":
        from .booknlp_adapter import BookNLPAdapter

        return BookNLPAdapter(
            engine_mode=engine_mode,
            model_name=model_name,
            pipeline_name=pipeline_name,
            native_temp_root=native_temp_root,
        )
    raise ValueError(f"unsupported language: {language}")
