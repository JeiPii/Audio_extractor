from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.config import AppConfig, get_backend_api_key
from app.extract import ExtractionError, ensure_ffmpeg_available, extract_audio, has_audio_stream
from app.formats import write_outputs
from app.models import TranscriptionResult
from app.transcribe_gemini import GeminiTranscriptionError, transcribe_gemini
from app.transcribe_local import LocalTranscriptionError, transcribe_local
from app.transcribe_openai import OpenAITranscriptionError, transcribe_openai


class PipelineError(RuntimeError):
    """Pipeline-level error with exit code classification."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(slots=True)
class ProcessSummary:
    input_path: Path
    output_files: list[Path]
    backend: str
    duration_seconds: float


def _validate_input_video(path: Path) -> None:
    if not path.exists():
        raise PipelineError(f"Input file does not exist: {path}", exit_code=2)
    if not path.is_file():
        raise PipelineError(f"Input path is not a file: {path}", exit_code=2)
    if path.suffix.lower() != ".mp4":
        raise PipelineError("Input must be an .mp4 file", exit_code=2)


def _transcribe_audio(audio_path: Path, config: AppConfig) -> TranscriptionResult:
    if config.backend == "local":
        try:
            return transcribe_local(audio_path, model=config.model, language=config.language, device=config.device)
        except LocalTranscriptionError as exc:
            raise PipelineError(str(exc), exit_code=4) from exc

    api_key = get_backend_api_key(config.backend)
    if not api_key:
        raise PipelineError(f"Missing API key for backend '{config.backend}'", exit_code=3)

    if config.backend == "openai":
        try:
            return transcribe_openai(audio_path, api_key=api_key, language=config.language)
        except OpenAITranscriptionError as exc:
            raise PipelineError(str(exc), exit_code=4) from exc

    try:
        return transcribe_gemini(audio_path, api_key=api_key, language=config.language)
    except GeminiTranscriptionError as exc:
        raise PipelineError(str(exc), exit_code=4) from exc


def process_video(input_path: Path, config: AppConfig) -> ProcessSummary:
    start = time.monotonic()

    _validate_input_video(input_path)

    try:
        ensure_ffmpeg_available()
        if not has_audio_stream(input_path):
            raise PipelineError("Input file has no audio stream", exit_code=2)
    except ExtractionError as exc:
        raise PipelineError(str(exc), exit_code=3) from exc

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="audio_extract_") as temp_dir:
        temp_audio = Path(temp_dir) / f"{input_path.stem}.wav"
        try:
            extract_audio(input_path, temp_audio)
        except ExtractionError as exc:
            raise PipelineError(str(exc), exit_code=4) from exc

        result = _transcribe_audio(temp_audio, config)

        if config.keep_audio:
            preserved_audio = output_dir / f"{input_path.stem}.wav"
            preserved_audio.write_bytes(temp_audio.read_bytes())

    base_output = output_dir / input_path.stem
    written = write_outputs(base_output, result, config.formats)

    return ProcessSummary(
        input_path=input_path,
        output_files=written,
        backend=config.backend,
        duration_seconds=time.monotonic() - start,
    )


def write_failure_marker(output_dir: Path, input_path: Path, message: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    marker = output_dir / f"{input_path.stem}.failed"
    marker.write_text(message.strip() + "\n", encoding="utf-8")
    return marker
