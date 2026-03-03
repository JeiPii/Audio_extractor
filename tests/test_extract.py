from pathlib import Path

from app.extract import build_extract_command, has_audio_stream


class DummyCompleted:
    def __init__(self, returncode: int, stdout: str, stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_build_extract_command() -> None:
    cmd = build_extract_command(Path("in.mp4"), Path("out.wav"))
    assert cmd[0] == "ffmpeg"
    assert "-ac" in cmd and "1" in cmd
    assert "-ar" in cmd and "16000" in cmd
    assert cmd[-1] == "out.wav"


def test_has_audio_stream_true(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return DummyCompleted(returncode=0, stdout='{"streams":[{"index":1}]}')

    monkeypatch.setattr("subprocess.run", fake_run)
    assert has_audio_stream(Path("video.mp4")) is True


def test_has_audio_stream_false(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return DummyCompleted(returncode=0, stdout='{"streams":[]}')

    monkeypatch.setattr("subprocess.run", fake_run)
    assert has_audio_stream(Path("video.mp4")) is False
