from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import Settings
from core.ffmpeg_builder import FFmpegBuilder


# --- Probe Video ---

class ProbeVideoInput(BaseModel):
    video_path: str = Field(description="Path to the video file to analyze")


class ProbeVideoTool(BaseTool):
    name: str = "probe_video"
    description: str = (
        "Gets metadata about a video file including duration, resolution (width x height), "
        "FPS, codec, and file size. Always use this before any editing operation "
        "to understand the video properties."
    )
    args_schema: Type[BaseModel] = ProbeVideoInput

    def _run(self, video_path: str) -> str:
        builder = FFmpegBuilder()
        metadata = builder.probe(video_path)
        return json.dumps(metadata, indent=2)


# --- Trim Video ---

class TrimVideoInput(BaseModel):
    input_path: str = Field(description="Path to the input video file")
    output_path: str = Field(description="Path for the trimmed output video")
    start_time: float = Field(description="Start time in seconds")
    end_time: float = Field(description="End time in seconds")


class TrimVideoTool(BaseTool):
    name: str = "trim_video"
    description: str = (
        "Trims a video file to keep only the segment between start_time and end_time "
        "(in seconds). Uses stream copy for fast, lossless trimming. "
        "Returns the path to the trimmed video on success."
    )
    args_schema: Type[BaseModel] = TrimVideoInput

    def _run(
        self, input_path: str, output_path: str, start_time: float, end_time: float
    ) -> str:
        start_time = float(start_time)
        end_time = float(end_time)
        builder = FFmpegBuilder()
        cmd = builder.trim(input_path, output_path, start_time, end_time)
        result = builder.execute(cmd)
        if result["success"]:
            return f"Video trimmed successfully: {output_path} ({end_time - start_time:.1f}s)"
        return f"Error trimming video: {result['stderr'][-300:]}"


# --- Concat Videos ---

class ConcatVideosInput(BaseModel):
    input_paths: list[str] = Field(
        description="List of video file paths to concatenate in order"
    )
    output_path: str = Field(description="Path for the concatenated output video")


class ConcatVideosTool(BaseTool):
    name: str = "concat_videos"
    description: str = (
        "Concatenates multiple video files into one continuous video without transitions. "
        "Videos must have the same codec, resolution, and frame rate. "
        "Uses stream copy for fast processing."
    )
    args_schema: Type[BaseModel] = ConcatVideosInput

    def _run(self, input_paths: list[str], output_path: str) -> str:
        builder = FFmpegBuilder()
        cmd = builder.concat_simple(input_paths, output_path)
        result = builder.execute(cmd)
        if result["success"]:
            return f"Videos concatenated successfully: {output_path}"
        return f"Error concatenating videos: {result['stderr'][-300:]}"


# --- Add Transition ---

class AddTransitionInput(BaseModel):
    input_paths: list[str] = Field(
        description="List of video file paths (at least 2) to join with transitions"
    )
    output_path: str = Field(description="Path for the output video with transitions")
    transition_type: str = Field(
        default="fade",
        description="Transition type: fade, dissolve, wipeleft, wiperight, slideleft, slideright",
    )
    transition_duration: float = Field(
        default=1.0,
        description="Duration of each transition in seconds",
    )


class AddTransitionTool(BaseTool):
    name: str = "add_transition"
    description: str = (
        "Joins multiple video clips with smooth transitions between them. "
        "Supports fade, dissolve, wipe, and slide transitions. "
        "Requires re-encoding so it takes longer than simple concatenation."
    )
    args_schema: Type[BaseModel] = AddTransitionInput

    def _run(
        self,
        input_paths: list[str],
        output_path: str,
        transition_type: str = "fade",
        transition_duration: float = 1.0,
    ) -> str:
        transition_duration = float(transition_duration)
        builder = FFmpegBuilder()
        cmd = builder.concat_with_transition(
            input_paths, output_path, transition_type, transition_duration
        )
        result = builder.execute(cmd, timeout=600)
        if result["success"]:
            return f"Videos joined with {transition_type} transitions: {output_path}"
        return f"Error adding transitions: {result['stderr'][-300:]}"


# --- Change Speed ---

class ChangeSpeedInput(BaseModel):
    input_path: str = Field(description="Path to the input video file")
    output_path: str = Field(description="Path for the speed-adjusted output video")
    speed_factor: float = Field(
        description="Speed multiplier: 2.0 = double speed, 0.5 = half speed"
    )


class ChangeSpeedTool(BaseTool):
    name: str = "change_speed"
    description: str = (
        "Changes the playback speed of a video. "
        "speed_factor of 2.0 doubles the speed (halves duration), "
        "0.5 halves the speed (doubles duration)."
    )
    args_schema: Type[BaseModel] = ChangeSpeedInput

    def _run(
        self, input_path: str, output_path: str, speed_factor: float
    ) -> str:
        speed_factor = float(speed_factor)
        builder = FFmpegBuilder()
        cmd = builder.change_speed(input_path, output_path, speed_factor)
        result = builder.execute(cmd, timeout=600)
        if result["success"]:
            return f"Speed changed to {speed_factor}x: {output_path}"
        return f"Error changing speed: {result['stderr'][-300:]}"


# --- Remove Silence ---

class RemoveSilenceInput(BaseModel):
    input_path: str = Field(description="Path to the input video file")
    output_path: str = Field(description="Path for the output video with silence removed")
    noise_db: float = Field(
        default=-35.0,
        description="Silence threshold in dB (e.g. -35.0). Lower = only remove very quiet parts.",
    )
    min_duration: float = Field(
        default=0.5,
        description="Minimum silence duration in seconds to remove (default 0.5s).",
    )


class RemoveSilenceTool(BaseTool):
    name: str = "remove_silence"
    description: str = (
        "Removes silent sections from a video. Useful for cleaning up talking-head "
        "videos, podcasts, interviews, or any video with unwanted pauses. "
        "Returns the path to the cleaned video on success."
    )
    args_schema: Type[BaseModel] = RemoveSilenceInput

    def _run(
        self,
        input_path: str,
        output_path: str,
        noise_db: float = -35.0,
        min_duration: float = 0.5,
    ) -> str:
        noise_db = float(noise_db)
        min_duration = float(min_duration)
        builder = FFmpegBuilder()
        cmd = builder.remove_silence(input_path, output_path, noise_db, min_duration)
        result = builder.execute(cmd, timeout=600)
        if result["success"]:
            return f"Silence removed successfully: {output_path}"
        return f"Error removing silence: {result['stderr'][-300:]}"


# --- Generate & Burn Subtitles ---

class GenerateSubtitlesInput(BaseModel):
    input_path: str = Field(description="Path to the input video file")
    output_path: str = Field(description="Path for the output video with burned-in subtitles")
    language: str = Field(
        default="en",
        description="Language code for transcription (e.g. 'en', 'es', 'fr', 'hi').",
    )


class GenerateSubtitlesTool(BaseTool):
    name: str = "generate_subtitles"
    description: str = (
        "Transcribes the video audio using OpenAI Whisper and burns the subtitles "
        "into the video. Works for any spoken language. Returns the path to the "
        "subtitled video on success."
    )
    args_schema: Type[BaseModel] = GenerateSubtitlesInput

    def _run(self, input_path: str, output_path: str, language: str = "en") -> str:
        settings = Settings()
        if not settings.use_openai:
            return "Error: OPENAI_API_KEY is required for subtitle generation."

        from pathlib import Path
        builder = FFmpegBuilder()
        srt_path = str(Path(output_path).with_suffix(".srt"))

        try:
            builder.generate_subtitles(input_path, srt_path, settings.openai_api_key, language)
        except Exception as e:
            return f"Error generating subtitles: {e}"

        cmd = builder.burn_subtitles(input_path, srt_path, output_path)
        result = builder.execute(cmd, timeout=600)
        if result["success"]:
            return f"Subtitles generated and burned into video: {output_path}"
        return f"Error burning subtitles: {result['stderr'][-300:]}"
