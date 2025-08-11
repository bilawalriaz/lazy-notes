# Lazy Notes — Local Audio-to-Notes Pipeline

Turn quick voice memos into clean, categorized, and tagged notes automatically. Drop an audio file into a folder; get Markdown + SQLite entries out. Local-first with faster-whisper and pluggable LLMs.

## Highlights

- Folder watcher for new audio files (watchdog)
- Robust audio normalization with ffmpeg (16kHz mono PCM)
- Transcription via faster-whisper (CPU by default; configurable)
- LLM post-processing: clean up text, generate title, category, and tags
- Providers supported: LM Studio, Ollama, or OpenRouter
- Structured outputs: transcript.json + processed.md + SQLite row

## Tech stack

- Python 3.12, watchdog, faster-whisper, requests, python-dotenv, SQLite
- ffmpeg for audio conversion
- LLM backends: LM Studio (OpenAI-compatible), Ollama, or OpenRouter

## Quick start

Prerequisites
- macOS (Apple Silicon works great; CPU-only by default)
- Homebrew (for ffmpeg) or another way to install ffmpeg
- This repo cloned locally

Install system dependency
```zsh
brew install ffmpeg
```

Option A) Use the bundled virtual environment
```zsh
source packages/bin/activate
pip install -r requirements.txt
```

Option B) Use your own virtual environment
```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Choose an LLM provider
- Open `main.py` and set `LLM_PROVIDER` to one of: `"lm_studio"`, `"ollama"`, or `"openrouter"`.
- If using OpenRouter, set the API key in your environment (e.g., via `.env`): `OPENROUTER_API_KEY=...`.
- Adjust model/temperature settings in `main.py` for your chosen provider.

Run the watcher
```zsh
python main.py
```

Drop audio files into `notes/input/`
- Supported containers/codecs handled via ffmpeg (e.g., .m4a, .mp3, .wav)
- The app converts to 16kHz mono WAV, transcribes, and then cleans/tags via the LLM

## What you get

For an input like `notes/input/My Idea.m4a`, the app creates:
- `notes/processed/2025-08-11_My_Idea/transcript.json` — raw transcript
- `notes/processed/2025-08-11_My_Idea/processed.md` — cleaned transcript + category + tags
- `notes.db` — a SQLite entry linking original audio, transcript, and processed note

Optionally inspect the DB
```zsh
sqlite3 notes.db ".mode box" "SELECT id, title, category, substr(tags,1,60) AS tags, created_at FROM notes ORDER BY id DESC LIMIT 10;"
```

## How it works

1) Watch `notes/input/` for new files
2) Normalize audio with ffmpeg (16kHz mono PCM WAV)
3) Transcribe with faster-whisper
4) Send transcript to your chosen LLM provider to:
  - Clean up text for readability (no summarization)
  - Suggest a concise title
  - Pick a single category
  - Generate tags
5) Save artifacts to `notes/processed/<date_title>/` and record a row in SQLite

## Configuration

Edit `main.py` to tweak behavior:
- `WHISPER_MODEL` — faster-whisper model size (e.g., `tiny`, `base`, `small`, `turbo`)
- `WHISPER_CPU_THREADS` — number of CPU threads for transcription
- LLM provider settings for LM Studio, Ollama, OpenRouter (URL, model, temperature)
- Prompt under “Please perform the following tasks:”

Folders
- Input: `notes/input/`
- Output: `notes/processed/<date_title>/`
- Database: `notes.db`

## Portfolio value

This project showcases:
- End-to-end automation with filesystem events
- Speech-to-text with faster-whisper and pragmatic audio preprocessing
- Multi-provider LLM integration (LM Studio, Ollama, OpenRouter)
- Data plumbing: structured file outputs and SQLite persistence
- Practical prompt engineering for deterministic formatting

## Troubleshooting

- ffmpeg not found: install via Homebrew (`brew install ffmpeg`) or your package manager
- LLM requests failing: ensure your chosen provider is running and credentials are set
- OpenRouter: set `OPENROUTER_API_KEY` in `.env` or your shell
- Nothing happens after placing a file: confirm the watcher is running (`python main.py`) and the file is in `notes/input/`

---

Local-first. Fast. Private. Ideal for journaling, research logs, and meeting notes.
