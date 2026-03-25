from __future__ import annotations

import re
import unicodedata
from datetime import datetime


def slugify_prompt(prompt: str, max_length: int = 48) -> str:
    normalized = unicodedata.normalize("NFKD", prompt).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower()
    lowered = lowered.replace("&", " and ")
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    compact = re.sub(r"-{2,}", "-", slug)
    compact = compact[:max_length].rstrip("-")
    return compact or "prompt"


def make_task_id(batch: str, ordinal: int) -> str:
    return f"{batch}-{ordinal:03d}"


def build_final_filename(
    batch: str,
    index: int,
    downloaded_at: datetime,
    prompt: str,
    extension: str = ".png",
    max_slug_length: int = 48,
) -> str:
    normalized_extension = extension if extension.startswith(".") else f".{extension}"
    timestamp = downloaded_at.strftime("%Y%m%dT%H%M%S")
    slug = slugify_prompt(prompt, max_length=max_slug_length)
    return f"{batch}_{index:03d}_{timestamp}_{slug}{normalized_extension}"
