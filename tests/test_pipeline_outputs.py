from pathlib import Path

from app.config import AppConfig
from app.models import Segment, TranscriptionResult
from app.pipeline import process_video


def test_pipeline_writes_txt_and_srt(monkeypatch, tmp_path: Path) -> None:
    video = tmp_path / "clip.mp4"
    video.write_text("fake-video", encoding="utf-8")

    monkeypatch.setattr("app.pipeline.ensure_ffmpeg_available", lambda: None)
    monkeypatch.setattr("app.pipeline.has_audio_stream", lambda _: True)

    def fake_extract(_input, output_audio):
        output_audio.write_bytes(b"WAV")
        return output_audio

    monkeypatch.setattr("app.pipeline.extract_audio", fake_extract)

    def fake_transcribe(_audio, config):
        return TranscriptionResult(
            language="en",
            segments=[Segment(start=0.0, end=1.2, text="hello world")],
        )

    monkeypatch.setattr("app.pipeline._transcribe_audio", fake_transcribe)

    cfg = AppConfig(output_dir=tmp_path, formats=("txt", "srt"))
    summary = process_video(video, cfg)

    out_txt = tmp_path / "clip.txt"
    out_srt = tmp_path / "clip.srt"

    assert out_txt in summary.output_files
    assert out_srt in summary.output_files
    assert "hello world" in out_txt.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,200" in out_srt.read_text(encoding="utf-8")
