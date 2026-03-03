from __future__ import annotations

import glob
from pathlib import Path
from typing import Annotated

import typer

from app.config import AppConfig, Backend, Device, parse_formats
from app.pipeline import PipelineError, process_video, write_failure_marker

app = typer.Typer(add_completion=False, help="Extract audio from MP4 and generate transcripts.")


def _resolve_batch_inputs(batch: str) -> list[Path]:
    batch_path = Path(batch)
    if batch_path.exists() and batch_path.is_dir():
        return sorted(batch_path.glob("*.mp4"))
    if batch_path.exists() and batch_path.is_file() and batch_path.suffix.lower() == ".mp4":
        return [batch_path]
    return sorted(Path(item) for item in glob.glob(batch))


@app.callback(invoke_without_command=True)
def transcribe_video(
    input_path: Annotated[Path | None, typer.Argument(help="Input MP4 file path")] = None,
    backend: Annotated[Backend, typer.Option("--backend", help="Transcription backend")] = "local",
    model: Annotated[str, typer.Option("--model", help="Model name")]= "medium",
    language: Annotated[str, typer.Option("--language", help="Language code or auto")] = "auto",
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Output directory")] = Path("output"),
    formats: Annotated[str, typer.Option("--formats", help="Comma-separated: txt,srt,vtt,json")] = "txt,srt",
    keep_audio: Annotated[bool, typer.Option("--keep-audio/--no-keep-audio", help="Keep extracted WAV")]=False,
    batch: Annotated[str | None, typer.Option("--batch", help="Directory or glob pattern for MP4 files")]=None,
    device: Annotated[Device, typer.Option("--device", help="Compute device")]= "auto",
) -> None:
    try:
        parsed_formats = parse_formats(formats)
    except ValueError as exc:
        typer.echo(f"Invalid formats: {exc}", err=True)
        raise typer.Exit(code=2)

    cfg = AppConfig(
        backend=backend,
        model=model,
        language=language,
        output_dir=output_dir,
        formats=parsed_formats,
        keep_audio=keep_audio,
        device=device,
    )

    if batch:
        files = _resolve_batch_inputs(batch)
        if not files:
            typer.echo("No MP4 files found for --batch input", err=True)
            raise typer.Exit(code=2)

        failures = 0
        for file_path in files:
            try:
                summary = process_video(file_path, cfg)
                typer.echo(
                    f"OK: {summary.input_path} -> {', '.join(str(p) for p in summary.output_files)} "
                    f"({summary.duration_seconds:.2f}s, backend={summary.backend})"
                )
            except PipelineError as exc:
                failures += 1
                marker = write_failure_marker(cfg.output_dir, file_path, str(exc))
                typer.echo(f"FAILED: {file_path} ({exc}) | marker={marker}", err=True)

        if failures:
            raise typer.Exit(code=4)
        return

    if input_path is None:
        typer.echo("Provide input_path or use --batch", err=True)
        raise typer.Exit(code=2)

    try:
        summary = process_video(input_path, cfg)
    except PipelineError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=exc.exit_code)

    typer.echo(
        f"OK: {summary.input_path} -> {', '.join(str(p) for p in summary.output_files)} "
        f"({summary.duration_seconds:.2f}s, backend={summary.backend})"
    )


def run() -> None:
    app()


if __name__ == "__main__":
    run()
