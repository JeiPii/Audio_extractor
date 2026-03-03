from __future__ import annotations

import json
from pathlib import Path

from app.models import Segment, TranscriptionResult


def format_srt_timestamp(seconds: float) -> str:
    millis = max(int(round(seconds * 1000.0)), 0)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def format_vtt_timestamp(seconds: float) -> str:
    millis = max(int(round(seconds * 1000.0)), 0)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{ms:03}"


def _safe_segment_end(segment: Segment) -> float:
    if segment.end < segment.start:
        return segment.start
    return segment.end


def write_txt(path: Path, result: TranscriptionResult) -> None:
    path.write_text(result.text + "\n", encoding="utf-8")


def write_srt(path: Path, result: TranscriptionResult) -> None:
    lines: list[str] = []
    for idx, segment in enumerate(result.segments, start=1):
        start = format_srt_timestamp(segment.start)
        end = format_srt_timestamp(_safe_segment_end(segment))
        lines.extend([str(idx), f"{start} --> {end}", segment.text.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_vtt(path: Path, result: TranscriptionResult) -> None:
    lines: list[str] = ["WEBVTT", ""]
    for segment in result.segments:
        start = format_vtt_timestamp(segment.start)
        end = format_vtt_timestamp(_safe_segment_end(segment))
        lines.extend([f"{start} --> {end}", segment.text.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, result: TranscriptionResult) -> None:
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_outputs(base_output_path: Path, result: TranscriptionResult, formats: tuple[str, ...]) -> list[Path]:
    written: list[Path] = []
    writers = {
        "txt": write_txt,
        "srt": write_srt,
        "vtt": write_vtt,
        "json": write_json,
    }

    for fmt in formats:
        output_path = base_output_path.with_suffix(f".{fmt}")
        writers[fmt](output_path, result)
        written.append(output_path)

    return written
