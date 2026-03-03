from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Backend = Literal["local", "openai", "gemini"]
Device = Literal["auto", "cpu", "cuda"]
Format = Literal["txt", "srt", "vtt", "json"]


@dataclass(slots=True)
class AppConfig:
    backend: Backend = "local"
    model: str = "medium"
    language: str = "auto"
    output_dir: Path = Path("output")
    formats: tuple[Format, ...] = ("txt", "srt")
    keep_audio: bool = False
    device: Device = "auto"


def parse_formats(raw: str | list[str] | tuple[str, ...]) -> tuple[Format, ...]:
    if isinstance(raw, str):
        candidates = [part.strip().lower() for part in raw.split(",") if part.strip()]
    else:
        candidates = [part.strip().lower() for part in raw if part.strip()]

    if not candidates:
        raise ValueError("At least one output format is required")

    allowed = {"txt", "srt", "vtt", "json"}
    unknown = [fmt for fmt in candidates if fmt not in allowed]
    if unknown:
        raise ValueError(f"Unsupported format(s): {', '.join(unknown)}")

    # Preserve order but remove duplicates.
    unique = tuple(dict.fromkeys(candidates).keys())
    return unique  # type: ignore[return-value]


def get_backend_api_key(backend: Backend) -> str | None:
    if backend == "openai":
        return os.getenv("OPENAI_API_KEY")
    if backend == "gemini":
        return os.getenv("GEMINI_API_KEY")
    return None
