from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.models import Segment, TranscriptionResult


class GeminiTranscriptionError(RuntimeError):
    """Raised when Gemini transcription fails."""


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
    raise GeminiTranscriptionError(f"Gemini transcription request failed after retries: {last_exc}")


def transcribe_gemini(
    audio_path: Path,
    api_key: str,
    language: str,
    model: str = "gemini-1.5-pro",
) -> TranscriptionResult:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise GeminiTranscriptionError(
            "google-generativeai package is not installed. Install optional dependency 'gemini'."
        ) from exc

    genai.configure(api_key=api_key)
    prompt = (
        "Transcribe this audio accurately. "
        "Return plain text only, preserving sentence boundaries."
    )
    if language != "auto":
        prompt += f" The spoken language is likely '{language}'."

    def _request() -> Any:
        uploaded = genai.upload_file(path=str(audio_path))
        model_client = genai.GenerativeModel(model_name=model)
        return model_client.generate_content([prompt, uploaded])

    response = _call_with_retry(_request)

    text = getattr(response, "text", None)
    if not text and getattr(response, "candidates", None):
        # Some SDK responses expose candidates instead of .text.
        text = str(response.candidates[0])

    clean_text = (text or "").strip()
    segments = [Segment(start=0.0, end=0.0, text=clean_text)]
    language_out = language if language != "auto" else "unknown"
    return TranscriptionResult(language=language_out, segments=segments)
