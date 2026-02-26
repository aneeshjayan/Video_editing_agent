from __future__ import annotations

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import Settings
from config.logging_config import logger

FILLER_WORDS = {
    "um", "uh", "uhh", "umm", "hmm", "hm", "er", "err",
    "like", "you know", "you know what i mean",
    "basically", "literally", "actually", "so", "right",
    "i mean", "kind of", "sort of", "okay so",
}


# --- Transcribe Audio ---

class TranscribeAudioInput(BaseModel):
    video_path: str = Field(description="Path to the video file to transcribe")
    language: str = Field(default="en", description="Language code, e.g. 'en', 'es', 'hi'")


class TranscribeAudioTool(BaseTool):
    name: str = "transcribe_audio"
    description: str = (
        "Transcribes the audio from a video using OpenAI Whisper. "
        "Returns a JSON string with the full transcript text and a list of segments, "
        "each with start_time, end_time, and text. "
        "Use this to get word-level timestamps for precision editing."
    )
    args_schema: Type[BaseModel] = TranscribeAudioInput

    def _run(self, video_path: str, language: str = "en") -> str:
        settings = Settings()
        if not settings.use_openai:
            return json.dumps({"error": "OPENAI_API_KEY required for transcription."})

        try:
            from openai import OpenAI
        except ImportError:
            return json.dumps({"error": "openai package not installed."})

        ffmpeg_path = settings.ffmpeg_path

        # Extract audio to temp mp3
        audio_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        audio_tmp.close()
        try:
            result = subprocess.run(
                [ffmpeg_path, "-y", "-i", video_path,
                 "-vn", "-acodec", "libmp3lame", "-q:a", "4", audio_tmp.name],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                return json.dumps({"error": f"Audio extraction failed: {result.stderr[-200:]}"})

            client = OpenAI(api_key=settings.openai_api_key)
            with open(audio_tmp.name, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    language=language,
                )

            segments = [
                {
                    "start_time": round(s.start, 2),
                    "end_time": round(s.end, 2),
                    "text": s.text.strip(),
                }
                for s in transcript.segments
            ]
            logger.info("Transcribed %d segments from %s", len(segments), video_path)
            return json.dumps({
                "text": transcript.text,
                "segments": segments,
                "language": transcript.language,
            }, indent=2)
        finally:
            os.unlink(audio_tmp.name)


# --- Detect Filler Words ---

class DetectFillerWordsInput(BaseModel):
    transcript_json: str = Field(
        description="JSON string from transcribe_audio containing 'segments' with timestamps"
    )


class DetectFillerWordsTool(BaseTool):
    name: str = "detect_filler_words"
    description: str = (
        "Analyzes a transcript (from transcribe_audio) and identifies segments containing "
        "filler words (um, uh, like, you know, basically, literally, etc.). "
        "Returns a JSON list of segments to cut, with start_time and end_time. "
        "Use the output to trim filler moments from the video."
    )
    args_schema: Type[BaseModel] = DetectFillerWordsInput

    def _run(self, transcript_json: str) -> str:
        try:
            data = json.loads(transcript_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid transcript JSON"})

        segments = data.get("segments", [])
        fillers_found = []

        for seg in segments:
            text_lower = seg.get("text", "").lower().strip()
            is_filler = (
                text_lower in FILLER_WORDS
                or any(f" {fw} " in f" {text_lower} " for fw in FILLER_WORDS)
                or (len(text_lower.split()) <= 3 and any(fw in text_lower for fw in {"um", "uh", "hmm", "er"}))
            )
            if is_filler:
                fillers_found.append({
                    "start_time": seg["start_time"],
                    "end_time": seg["end_time"],
                    "text": seg["text"],
                })

        logger.info("Found %d filler segments", len(fillers_found))
        return json.dumps({
            "filler_count": len(fillers_found),
            "fillers": fillers_found,
            "total_filler_duration": round(
                sum(f["end_time"] - f["start_time"] for f in fillers_found), 2
            ),
        }, indent=2)
