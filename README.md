# Audio Extractor + Transcriber CLI

Python CLI to:
1. Extract audio from MP4 using `ffmpeg`.
2. Transcribe audio with local `faster-whisper` (default), or optional OpenAI/Gemini backends.
3. Write transcript outputs (`txt`, `srt`, optional `vtt`, `json`).

## Requirements

- Python 3.11+
- `ffmpeg` and `ffprobe` installed and available in `PATH`

Install dependencies:
The quickest install is to go to the root folder of Audio_extractor where the pyproject.toml is located and use the `pipx install -e .` 
From this moment you can use the newly added transcribe-video command.

If you need guidance for Pipx installation follow the following guide:
https://pipx.pypa.io/stable/installation/

## Usage

Single file:

```bash
transcribe-video /path/to/video.mp4
```

Single file with options:

```bash
transcribe-video /path/to/video.mp4 \
  --backend local \
  --model medium \
  --language auto \
  --output-dir ./output \
  --formats txt,srt \
  --device auto
```

Batch mode (directory or glob):

```bash
transcribe-video --batch "/path/to/videos/*.mp4" --output-dir ./output
```

### CLI Options

- `--backend {local,openai,gemini}` default `local`
- `--model {tiny,base,small,medium,large-v3}` default `medium`
- `--language <code|auto>` default `auto`
- `--output-dir <path>` default `./output`
- `--formats <txt,srt,vtt,json>` default `txt,srt`
- `--keep-audio/--no-keep-audio` default `--no-keep-audio`
- `--batch <glob_or_dir>` optional batch mode
- `--device {auto,cpu,cuda}` default `auto`

## API Keys

Set keys only when using cloud backends:

```bash
export OPENAI_API_KEY="..."
export GEMINI_API_KEY="..."
```

## Exit Codes

- `0`: success
- `2`: invalid input/arguments
- `3`: dependency/config error
- `4`: transcription failure

## Notes on Cost and Subscriptions

- Local backend (`faster-whisper`) is free per-use after setup.
- OpenAI and Gemini backend usage is billed via their API credentials.
- A ChatGPT subscription does not automatically include OpenAI API usage credits.

## Troubleshooting

- `ffmpeg is not installed`: install `ffmpeg` and ensure it is in `PATH`.
- `Input file has no audio stream`: verify the MP4 contains audio.
- `Missing API key for backend`: export the backend key before running.
- Slow local transcription: use `--model small` or `--device cuda` when GPU is available.

## Test

```bash
pytest -q
```
