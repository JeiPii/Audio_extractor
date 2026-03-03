from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.models import Segment, TranscriptionResult


class OpenAITranscriptionError(RuntimeError):
    """Raised when OpenAI transcription fails."""


def _call_with_retry(func, max_retries: int = 3) -> Any:
    delay_seconds = 1.0
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as exc:  # pragma: no cover - depends on SDK/HTTP runtime
            last_exc = exc
            if attempt == max_retries - 1:
                break
            time.sleep(delay_seconds)
            delay_seconds *= 2
    raise OpenAITranscriptionError(f"OpenAI transcription request failed after retries: {last_exc}")


def transcribe_openai(
    audio_path: Path,
    api_key: str,
    language: str,
    model: str = "gpt-4o-transcribe",
) -> TranscriptionResult:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise OpenAITranscriptionError(
            "openai package is not installed. Install optional dependency 'openai'."
        ) from exc

    selected_language = None if language == "auto" else language
    client = OpenAI(api_key=api_key)

    def _request() -> Any:
        with audio_path.open("rb") as audio_file:
            return client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                language=selected_language,
            )

    response = _call_with_retry(_request)

    language_out = getattr(response, "language", None) or "unknown"
    raw_segments = getattr(response, "segments", None)
    text = getattr(response, "text", "")

    if raw_segments:
        segments = [
            Segment(
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", seg.get("start", 0.0))),
                text=str(seg.get("text", "")).strip(),
            )
            for seg in raw_segments
        ]
    else:
        # Fallback when provider does not return segment timestamps.
        segments = [Segment(start=0.0, end=0.0, text=str(text).strip())]

    return TranscriptionResult(language=language_out, segments=segments)
