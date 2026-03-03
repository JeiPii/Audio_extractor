from pathlib import Path

import pytest

from app.config import AppConfig, parse_formats
from app.pipeline import PipelineError, process_video


def test_parse_formats_and_deduplicate() -> None:
    result = parse_formats("txt,srt,txt")
    assert result == ("txt", "srt")


def test_parse_formats_invalid() -> None:
    with pytest.raises(ValueError):
        parse_formats("txt,doc")


def test_pipeline_invalid_extension(tmp_path: Path) -> None:
    bad = tmp_path / "bad.txt"
    bad.write_text("x", encoding="utf-8")

    with pytest.raises(PipelineError) as exc:
        process_video(bad, AppConfig())

    assert exc.value.exit_code == 2


def test_pipeline_missing_api_key_for_openai(tmp_path: Path, monkeypatch) -> None:
    video = tmp_path / "clip.mp4"
    video.write_text("fake", encoding="utf-8")

    monkeypatch.setattr("app.pipeline.ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr("app.pipeline.has_audio_stream", lambda _: True)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cfg = AppConfig(backend="openai")
    with pytest.raises(PipelineError) as exc:
        process_video(video, cfg)

    assert exc.value.exit_code == 3
