from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class ExtractionError(RuntimeError):
    """Raised when audio extraction fails."""


def ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        raise ExtractionError("ffmpeg is not installed or not available in PATH")
    if shutil.which("ffprobe") is None:
        raise ExtractionError("ffprobe is not installed or not available in PATH")


def build_extract_command(input_path: Path, output_wav_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_wav_path),
    ]


def has_audio_stream(input_path: Path) -> bool:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=index",
        "-of",
        "json",
        str(input_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ExtractionError(f"ffprobe failed: {proc.stderr.strip()}")

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ExtractionError("ffprobe output could not be parsed") from exc

    return bool(payload.get("streams"))


def extract_audio(input_path: Path, output_wav_path: Path) -> Path:
    cmd = build_extract_command(input_path, output_wav_path)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise ExtractionError(f"ffmpeg extraction failed: {stderr}")
    return output_wav_path
