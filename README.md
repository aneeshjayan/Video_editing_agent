# AI Video Editor Agent

A multi-agent AI video editor powered by **CrewAI**, **OpenAI/Ollama**, and **FFmpeg**. Edit videos using plain English instructions — no video editing skills required.

---

## Features

- **Natural language editing** — describe what you want, the AI figures out the rest
- **Multi-agent pipeline** — specialized agents for audio intelligence, scene detection, narrative structure, and platform adaptation
- **Smart routing** — automatically selects a 3-agent or 6-agent pipeline based on task complexity
- **Local-first option** — run fully offline with Ollama (no API keys needed)
- **Platform reframing** — one-click conversion to YouTube Shorts, TikTok, Instagram Reels, and more
- **Auto-subtitles** — Whisper-powered transcription burned directly into video
- **Silence removal** — detect and strip dead air automatically
- **Dual interface** — Streamlit web UI or FastAPI REST backend

---

## Architecture

The system routes instructions to one of three pipelines:

| Pipeline | Agents | Use Case |
|---|---|---|
| **Simple** | 2 | Trim, speed, silence removal, subtitles |
| **Standard** | 3 | Vision-aware edits with content analysis |
| **Full** | 6 | Highlight reels, platform adaptation, filler removal |

**Full pipeline agents:**
1. **Orchestrator** — coordinates the workflow
2. **Audio Intelligence** — transcription, filler word detection
3. **Scene Detection** — identifies visual boundaries
4. **Clip Trimmer** — removes low-quality segments
5. **Narrative Structurer** — plans hook / body / closing
6. **Platform Adapter** — reframes for target platform

---

## Prerequisites

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) installed and in your PATH
- OpenAI API key **or** [Ollama](https://ollama.com/download) running locally

**Install FFmpeg:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd "Video editing agent"

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
# or
pip install -r requirements.txt
```

---

## Configuration

Copy the example env file and fill in your settings:

```bash
cp .env.example .env
```

```ini
# .env

# OpenAI (recommended for best results)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini           # Fast planning model
OPENAI_VISION_MODEL=gpt-4o         # Vision analysis model

# Ollama (local, no API key required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_VISION_MODEL=llama3.2-vision

# Video processing
MAX_VIDEO_SIZE_MB=500
FRAME_EXTRACTION_INTERVAL=5.0      # Seconds between extracted frames
TEMP_DIR=./tmp
FFMPEG_PATH=ffmpeg
```

Leave `OPENAI_API_KEY` empty to automatically fall back to Ollama.

---

## Running the App

### Streamlit Web UI (recommended)

```bash
streamlit run ui/app.py
```

Opens at [http://localhost:8501](http://localhost:8501). Upload a video, choose a platform target, type your instruction, and click **Edit**.

### FastAPI REST Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
```

Interactive docs at [http://localhost:8080/docs](http://localhost:8080/docs).

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/jobs` | Submit an editing job |
| `GET` | `/api/jobs/{job_id}` | Poll job status |
| `GET` | `/api/jobs/{job_id}/download` | Download the result |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/platforms` | List available platform presets |

### CLI Demo

```bash
python scripts/demo.py --video input.mp4 --instruction "trim first 10 seconds"
python scripts/demo.py --video input.mp4 --instruction "create a 30-second highlight reel"
```

### Fully Local with Ollama

```bash
ollama pull llama3.2
ollama pull llama3.2-vision
# Leave OPENAI_API_KEY blank in .env, then run as normal
```

---

## Example Instructions

```
"Trim the first 10 seconds and last 5 seconds"
"Remove all silent sections"
"Speed up to 1.5x"
"Add subtitles"
"Create a 30-second highlight reel"
"Remove filler words and awkward pauses"
"Reframe for YouTube Shorts"
"Make a TikTok version of the best moments"
```

---

## Platform Presets

| Platform | Aspect Ratio | Resolution |
|---|---|---|
| YouTube | 16:9 | 1920×1080 |
| YouTube Shorts | 9:16 | 1080×1920 |
| Instagram Reels | 9:16 | 1080×1920 |
| TikTok | 9:16 | 1080×1920 |
| Instagram Square | 1:1 | 1080×1080 |
| Original | — | Keep source |

---

## Edit Explanation

After every edit, the system generates a human-readable summary of what was done:

```
• [00:00 – 00:04] KEPT: Strong opening hook
• [00:12 – 00:15] REMOVED: 3s silence gap
• [00:23 – 00:24] REMOVED: Filler words
• [ALL] REFRAMED: 16:9 → 9:16 for YouTube Shorts
• Final output: 45s → 38s
```

---

## Project Structure

```
.
├── agents/          # CrewAI agent definitions & pipeline orchestration
├── api/             # FastAPI REST backend
├── config/          # Settings, prompts, logging
├── core/            # FFmpeg builder, scene detector, frame extractor
├── frontend/        # (reserved for future standalone frontend)
├── models/          # Pydantic schemas and enums
├── scripts/         # CLI demo script
├── services/        # External service integrations (vision API)
├── tests/           # pytest test suite
├── tools/           # CrewAI tool implementations
├── ui/              # Streamlit web interface
├── tmp/             # Temporary files (auto-created)
├── requirements.txt
└── pyproject.toml
```

---

## Running Tests

```bash
pytest tests/
pytest tests/ -v                        # Verbose output
pytest tests/test_core/ -k trim         # Run specific tests
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | CrewAI |
| LLM / Vision | OpenAI GPT-4o, GPT-4o-mini |
| Local LLM | Ollama (llama3.2, llama3.2-vision) |
| Transcription | OpenAI Whisper |
| Video processing | FFmpeg, ffmpeg-python |
| Scene detection | OpenCV |
| Image processing | Pillow |
| Web UI | Streamlit |
| REST API | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Linting | Ruff |
| Testing | pytest, pytest-mock |

---

## Limits & Defaults

| Setting | Default | Configurable |
|---|---|---|
| Max video size | 500 MB | `MAX_VIDEO_SIZE_MB` |
| Frame extraction | Every 5s | `FRAME_EXTRACTION_INTERVAL` |
| FFmpeg timeout | 300s | In `FFmpegBuilder` |
| Concurrent API jobs | 4 | `ThreadPoolExecutor` in `api/main.py` |

---

## License

This project is in active development. See the repository for license details.
