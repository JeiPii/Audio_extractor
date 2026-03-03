from __future__ import annotations

from pathlib import Path

from app.models import Segment, TranscriptionResult


class LocalTranscriptionError(RuntimeError):
    """Raised when local transcription fails."""


def transcribe_local(
    audio_path: Path,
    model: str,
    language: str,
    device: str,
) -> TranscriptionResult:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise LocalTranscriptionError(
            "faster-whisper is not installed. Install project dependencies first."
        ) from exc

    selected_language = None if language == "auto" else language

    try:
        whisper_model = WhisperModel(model_size_or_path=model, device=device, compute_type="int8")
        segments_iter, info = whisper_model.transcribe(
            str(audio_path),
            language=selected_language,
            vad_filter=True,
        )
        segments = [
            Segment(
                start=float(segment.start),
                end=float(segment.end),
                text=str(segment.text).strip(),
            )
            for segment in segments_iter
        ]
    except Exception as exc:  # pragma: no cover - library/runtime dependent
        raise LocalTranscriptionError(f"Local transcription failed: {exc}") from exc

    return TranscriptionResult(language=getattr(info, "language", selected_language or "unknown"), segments=segments)
