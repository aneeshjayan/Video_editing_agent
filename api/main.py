"""FastAPI backend for the AI Video Editor.

Replaces the Streamlit UI as the server-side entry point.
Supports GCS (when GCS_BUCKET env var is set) or local filesystem.

Run locally:
    uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload
"""
from __future__ import annotations

import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from tools.platform_tools import PLATFORM_PRESETS

app = FastAPI(title="AI Video Editor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (use Firestore/Redis for multi-instance production)
_jobs: dict[str, dict] = {}
_executor = ThreadPoolExecutor(max_workers=4)

# ── Temp directory ────────────────────────────────────────────────────────────
_TMP = _ROOT / "tmp"
_TMP.mkdir(exist_ok=True)


# ── Health & metadata ─────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/platforms")
def get_platforms():
    return JSONResponse(PLATFORM_PRESETS)


# ── Job submission ─────────────────────────────────────────────────────────────

@app.post("/api/jobs")
async def submit_job(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    instruction: str = Form(...),
    platform: str = Form("original"),
    add_subtitles: bool = Form(False),
):
    """Upload video(s) and kick off the editing pipeline."""
    if not instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    job_id = str(uuid.uuid4())[:8]
    job_dir = _TMP / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Persist uploaded files synchronously before returning
    video_paths: list[str] = []
    for i, upload in enumerate(files):
        suffix = Path(upload.filename or "video").suffix or ".mp4"
        dest = job_dir / f"input_{i}{suffix}"
        dest.write_bytes(await upload.read())
        video_paths.append(str(dest.resolve()))

    _jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "logs": [],
        "output_url": None,
        "error": None,
        "edit_explanation": None,
        "crew_output": None,
    }

    background_tasks.add_task(
        _run_pipeline, job_id, video_paths, instruction, platform, add_subtitles
    )
    return {"job_id": job_id}


# ── Job status & download ─────────────────────────────────────────────────────

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet.")

    output_path = job.get("output_path")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=404, detail="Output file not found.")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"edited_{job_id}.mp4",
    )


# ── Pipeline runner (runs in thread pool) ─────────────────────────────────────

def _run_pipeline(
    job_id: str,
    video_paths: list[str],
    instruction: str,
    platform: str,
    add_subtitles: bool,
) -> None:
    from agents.flow import VideoEditFlow

    def on_progress(state):
        _jobs[job_id].update(
            {
                "status": str(state.status),
                "progress": state.progress_percent,
                "logs": list(state.logs),
            }
        )

    try:
        flow = VideoEditFlow()
        result = flow.run(
            video_paths=video_paths,
            user_instruction=instruction,
            platform=platform,
            add_subtitles=add_subtitles,
            progress_callback=on_progress,
        )

        output_path: Optional[str] = result.output_path or None

        _jobs[job_id].update(
            {
                "status": str(result.status),
                "progress": result.progress_percent,
                "logs": list(result.logs),
                "output_path": output_path,
                # Expose download URL (frontend polls this and constructs download link)
                "output_url": f"/api/jobs/{job_id}/download" if output_path else None,
                "error": result.error or None,
                "edit_explanation": result.edit_explanation or None,
                "crew_output": result.crew_output or None,
            }
        )
    except Exception as exc:  # noqa: BLE001
        _jobs[job_id].update(
            {
                "status": "failed",
                "error": str(exc),
                "logs": _jobs[job_id].get("logs", []) + [f"Fatal error: {exc}"],
            }
        )
