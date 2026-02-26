from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agents.crew import create_video_editing_crew
from config.logging_config import logger
from config.settings import Settings
from core.ffmpeg_builder import FFmpegBuilder
from models.enums import PipelineStage, PipelineStatus

# Instructions that only need timestamps — no visual content understanding required
_SIMPLE_EDIT_PATTERNS = [
    r"trim\s+(first|last)\s+\d+",
    r"remove\s+(first|last)\s+\d+",
    r"keep\s+(first|last)\s+\d+",
    r"cut\s+(first|last)\s+\d+",
    r"\d+x?\s*speed",
    r"speed\s*up",
    r"slow\s*down",
    r"remove\s+silence",
    r"add\s+subtitles?",
    r"generate\s+subtitles?",
]

# Instructions that warrant the full 6-agent pipeline
_FULL_PIPELINE_PATTERNS = [
    r"highlight\s*reel",
    r"youtube\s*short",
    r"instagram\s*reel",
    r"tiktok",
    r"short[s]?\s*(video|clip|form)",
    r"remove\s+filler",
    r"clean\s*up\s*speech",
    r"best\s+moments",
    r"60\s*second",
    r"30\s*second",
    r"platform",
    r"vertical",
    r"reframe",
    r"portrait",
]


def _needs_vision(instruction: str) -> bool:
    text = instruction.lower()
    return not any(re.search(p, text) for p in _SIMPLE_EDIT_PATTERNS)


def _needs_full_pipeline(instruction: str) -> bool:
    text = instruction.lower()
    return any(re.search(p, text) for p in _FULL_PIPELINE_PATTERNS)


class VideoEditState(BaseModel):
    """Tracks the full state of a video editing pipeline run."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    video_paths: list[str] = Field(default_factory=list)
    user_instruction: str = ""
    platform: str = "original"
    add_subtitles: bool = False

    # Pipeline tracking
    current_stage: PipelineStage = PipelineStage.UPLOAD
    status: PipelineStatus = PipelineStatus.PENDING
    progress_percent: int = 0

    # Results
    video_metadata: dict = Field(default_factory=dict)
    output_path: str = ""
    crew_output: str = ""
    edit_explanation: str = ""   # Human-readable AI summary of what was edited
    error: str = ""
    logs: list[str] = Field(default_factory=list)


class VideoEditFlow:
    """Orchestrates the full video editing pipeline."""

    def __init__(self):
        self.settings = Settings()
        self.state = VideoEditState()

    def _log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.state.logs.append(f"[{timestamp}] {message}")
        logger.info(message)

    def _update_stage(self, stage: PipelineStage, progress: int) -> None:
        self.state.current_stage = stage
        self.state.progress_percent = progress

    def _generate_explanation(self, crew_output: str, metadata: dict) -> str:
        """Ask OpenAI to summarize the edits made in plain English with timestamps."""
        if not self.settings.use_openai:
            self._log("Skipping edit explanation — no OpenAI API key configured.")
            return ""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.settings.openai_api_key)
            duration = metadata.get("duration", 0)
            prompt = (
                f"You are a video editor assistant. Based on the agent pipeline output below, "
                f"write a clear, structured explanation of every edit that was made to the video.\n\n"
                f"Original video duration: {duration:.1f}s\n"
                f"User instruction: {self.state.user_instruction}\n"
                f"Platform: {self.state.platform}\n\n"
                f"Agent pipeline output:\n{crew_output[:4000]}\n\n"
                f"Write a bullet-point summary in this exact format:\n"
                f"• [MM:SS – MM:SS] ACTION: brief explanation\n\n"
                f"Examples:\n"
                f"• [00:00 – 00:04] KEPT: Strong opening hook — man introducing topic\n"
                f"• [00:12 – 00:15] REMOVED: 3s silence gap\n"
                f"• [00:23 – 00:24] REMOVED: Filler words ('um', 'you know')\n"
                f"• [01:06 – 01:16] TRIMMED: Last 10 seconds removed as requested\n"
                f"• [ALL] REFRAMED: Converted 16:9 → 9:16 for YouTube Shorts\n"
                f"• [ALL] SUBTITLES: Auto-generated captions added\n\n"
                f"End with one line: 'Final output: Xs → Ys' showing original vs final duration.\n"
                f"If you don't have exact timestamps from the output, estimate based on what was done."
            )
            response = client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3,
            )
            explanation = response.choices[0].message.content.strip()
            self._log("Edit explanation generated successfully.")
            return explanation
        except Exception as e:
            self._log(f"Could not generate edit explanation: {e}")
            logger.warning("Could not generate explanation: %s", e)
            return ""

    def run(
        self,
        video_paths: list[str] | str,
        user_instruction: str,
        platform: str = "original",
        add_subtitles: bool = False,
        progress_callback: Any = None,
    ) -> VideoEditState:
        # Normalize to list
        if isinstance(video_paths, str):
            video_paths = [video_paths]

        self.state.video_paths = video_paths
        self.state.user_instruction = user_instruction
        self.state.platform = platform
        self.state.add_subtitles = add_subtitles
        self.state.status = PipelineStatus.IN_PROGRESS

        def notify():
            if progress_callback:
                progress_callback(self.state)

        try:
            self._update_stage(PipelineStage.UPLOAD, 5)
            self._log(f"Starting job {self.state.job_id}")
            self._log(f"Videos: {len(video_paths)} file(s)")
            self._log(f"Instruction: {user_instruction}")
            self._log(f"Platform: {platform}")
            notify()

            builder = FFmpegBuilder(self.settings.ffmpeg_path)
            temp_dir = str(
                (Path(self.settings.temp_dir) / self.state.job_id).resolve()
            )
            Path(temp_dir).mkdir(parents=True, exist_ok=True)

            # Resolve all paths to absolute
            abs_paths = [str(Path(p).resolve()) for p in video_paths]

            # If multiple videos, concatenate them first
            if len(abs_paths) > 1:
                self._log(f"Concatenating {len(abs_paths)} videos...")
                merged_path = f"{temp_dir}\\merged_input.mp4"
                concat_cmd = builder.concat_simple(abs_paths, merged_path)
                result = builder.execute(concat_cmd)
                if not result["success"]:
                    raise RuntimeError(f"Failed to merge videos: {result['stderr'][-200:]}")
                primary_path = merged_path
                self._log(f"Videos merged: {merged_path}")
            else:
                primary_path = abs_paths[0]

            # Probe the primary video
            metadata = builder.probe(primary_path)
            self.state.video_metadata = metadata
            self._log(
                f"Video: {metadata['duration']:.1f}s, "
                f"{metadata['width']}x{metadata['height']}, "
                f"{metadata['fps']}fps"
            )

            # Decide which pipeline to use
            use_full = _needs_full_pipeline(user_instruction) or platform != "original"
            skip_vision = not _needs_vision(user_instruction)
            llm_label = self.settings.openai_model if self.settings.use_openai else self.settings.ollama_model

            self._update_stage(PipelineStage.CONTENT_ANALYSIS, 15)
            if use_full:
                self._log(f"Full 6-agent pipeline ({llm_label}): Orchestrator → Audio → Scene → Trimmer → Narrative → Platform")
            elif skip_vision:
                self._log(f"Simple edit ({llm_label}): Script Writer → Executor")
            else:
                self._log(f"Standard pipeline ({llm_label}): Analyzer → Script Writer → Executor")
            notify()

            crew = create_video_editing_crew(
                video_path=primary_path,
                user_instruction=user_instruction,
                video_duration=metadata["duration"],
                video_width=metadata["width"],
                video_height=metadata["height"],
                temp_dir=temp_dir,
                skip_vision=skip_vision,
                use_full_pipeline=use_full,
                platform=platform,
                add_subtitles=add_subtitles,
                num_videos=len(abs_paths),
            )

            self._update_stage(PipelineStage.EXECUTION, 40)
            notify()

            result = crew.kickoff()
            self.state.crew_output = str(result)

            self._update_stage(PipelineStage.DELIVERY, 90)
            self._log("Crew completed. Generating edit explanation...")
            notify()

            # Generate human-readable explanation of what was edited
            self.state.edit_explanation = self._generate_explanation(
                str(result), metadata
            )

            # Prefer output.mp4, fallback to most recently modified mp4
            output_files = list(Path(temp_dir).glob("*.mp4"))
            if output_files:
                named_output = Path(temp_dir) / "output.mp4"
                if named_output.exists():
                    self.state.output_path = str(named_output)
                else:
                    self.state.output_path = str(
                        max(output_files, key=lambda p: p.stat().st_mtime)
                    )
                self._log(f"Output: {self.state.output_path}")

            self._update_stage(PipelineStage.DELIVERY, 100)
            self.state.status = PipelineStatus.COMPLETED
            self._log("Pipeline completed successfully!")
            notify()

        except Exception as e:
            self.state.status = PipelineStatus.FAILED
            self.state.error = str(e)
            self._log(f"Pipeline failed: {e}")
            logger.exception("Pipeline error")
            notify()

        return self.state
