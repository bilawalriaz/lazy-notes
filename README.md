# Local Notes Transcribe

Drop an audio file into a folder and get a cleaned, categorized, and tagged note—automatically. Runs locally with Whisper on Apple Silicon and an LLM served by LM Studio.

## Quick start

Prerequisites
- macOS (Apple Silicon recommended for MPS)
- LM Studio installed (and a local model ready to serve)
- This repo cloned locally

Steps
1) Activate the bundled virtual environment

```zsh
source packages/bin/activate
```

2) Start LM Studio’s local server
- Open LM Studio
- Select a chat/instruct model (e.g., Qwen, Llama, Mistral, etc.)
- Start the local server on http://localhost:1234

3) Run the watcher

```zsh
python main.py
```

4) Drop an audio file into `notes/input/`
- Supported: .wav, .mp3, .mp4, .m4a
- The app will detect the new file, transcribe it, then clean and categorize it using the LLM.

## What you get
For an input like `notes/input/My Idea.m4a`, the app creates:
- `notes/processed/My Idea/transcript.json` — raw Whisper transcript
- `notes/processed/My Idea/processed.md` — cleaned transcript + category + tags
- `notes.db` — a SQLite entry linking original audio, transcript, and processed note

View the DB (optional)
```zsh
sqlite3 notes.db ".mode box" "SELECT id, category, tags, created_at FROM notes ORDER BY id DESC LIMIT 10;"
```

## How it works
- Watches `notes/input/` for new files (watchdog)
- Transcribes audio with `whisper-mps` (Apple Metal acceleration)
- Calls LM Studio’s OpenAI-compatible endpoint (`/v1/chat/completions`) to:
  - Clean up the transcript
  - Pick a single category
  - Generate tags
- Saves artifacts and logs the note in SQLite

## Configuration
Edit `main.py` to tweak behavior:
- `WHISPER_MODEL` — Whisper size (e.g., `tiny`, `base`, `small`, …)
- `LM_STUDIO_API_URL` — change if LM Studio is on another port or host
- Prompt — adjust the instructions under “Please perform the following tasks:”

Folders
- Input: `notes/input/`
- Output: `notes/processed/<audio-basename>/`
- Database: `notes.db`

## Tips
- The watcher triggers on new files. To reprocess an existing file, drop a copy or rename it.
- Run from the repository root so `whisper-mps` writes `output.json` where the app expects it.
- Ensure the virtual environment is active so `whisper-mps` and Python deps resolve.

## Troubleshooting
- LLM call failing (404/connection): Start LM Studio server on port 1234 and keep it running.
- `whisper-mps: command not found`: `source packages/bin/activate` first. If you prefer your own env, install `watchdog` and ensure a Whisper CLI that outputs `output.json` (this project uses `whisper-mps`).
- Nothing happens after placing a file: Confirm the watcher is running (`python main.py`) and you placed the file in `notes/input/`.
- Permission or path errors: Make sure you’re in the project root when running the script.

## Why this setup?
- Local-first, private processing
- Fast transcription using Apple Metal (MPS)
- Flexible LLM post-processing via LM Studio

Happy noting!
