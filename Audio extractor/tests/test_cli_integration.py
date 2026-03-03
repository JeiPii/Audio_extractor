from pathlib import Path

from typer.testing import CliRunner

from app.cli import app
from app.pipeline import PipelineError, ProcessSummary

runner = CliRunner()


def test_single_file_success(monkeypatch, tmp_path: Path) -> None:
    video = tmp_path / "one.mp4"
    video.write_text("video", encoding="utf-8")

    expected_output = tmp_path / "out.txt"

    def fake_process(path, cfg):
        return ProcessSummary(
            input_path=path,
            output_files=[expected_output],
            backend=cfg.backend,
            duration_seconds=0.5,
        )

    monkeypatch.setattr("app.cli.process_video", fake_process)

    result = runner.invoke(app, [str(video), "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "OK:" in result.stdout


def test_batch_mixed_success_failure(monkeypatch, tmp_path: Path) -> None:
    ok_video = tmp_path / "ok.mp4"
    bad_video = tmp_path / "bad.mp4"
    ok_video.write_text("ok", encoding="utf-8")
    bad_video.write_text("bad", encoding="utf-8")

    def fake_process(path, cfg):
        if path.name == "bad.mp4":
            raise PipelineError("boom", exit_code=4)
        return ProcessSummary(
            input_path=path,
            output_files=[tmp_path / f"{path.stem}.txt"],
            backend=cfg.backend,
            duration_seconds=0.2,
        )

    monkeypatch.setattr("app.cli.process_video", fake_process)

    result = runner.invoke(app, ["--batch", str(tmp_path), "--output-dir", str(tmp_path)])
    assert result.exit_code == 4
    assert "FAILED:" in result.stdout
    assert (tmp_path / "bad.failed").exists()
