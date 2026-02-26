from __future__ import annotations

import json
import subprocess
from pathlib import Path

import ffmpeg

from config.logging_config import logger
from core.exceptions import FFmpegError


class FFmpegBuilder:
    """Generates and executes FFmpeg commands from edit operations."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def probe(self, video_path: str) -> dict:
        """Get video metadata using ffprobe."""
        try:
            probe_data = ffmpeg.probe(video_path)
        except ffmpeg.Error as e:
            raise FFmpegError(f"ffprobe failed for {video_path}: {e.stderr}") from e

        video_stream = next(
            (s for s in probe_data["streams"] if s["codec_type"] == "video"),
            None,
        )
        if video_stream is None:
            raise FFmpegError(f"No video stream found in {video_path}")

        # Parse frame rate from fraction string like "30/1"
        fps_str = video_stream.get("r_frame_rate", "30/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / float(den)
        else:
            fps = float(fps_str)

        return {
            "duration": float(probe_data["format"].get("duration", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": round(fps, 2),
            "codec": video_stream.get("codec_name", "unknown"),
            "size": int(probe_data["format"].get("size", 0)),
        }

    def trim(
        self,
        input_path: str,
        output_path: str,
        start: float,
        end: float,
    ) -> list[str]:
        """Build an FFmpeg trim command.

        Returns command as list of args for subprocess.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-ss", str(start),
            "-to", str(end),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            output_path,
        ]
        logger.info("Trim command: %s", " ".join(cmd))
        return cmd

    def concat_simple(
        self,
        input_paths: list[str],
        output_path: str,
    ) -> list[str]:
        """Concatenate videos using the concat demuxer (no re-encoding)."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Create concat list file
        list_path = str(Path(output_path).parent / "concat_list.txt")
        with open(list_path, "w") as f:
            for path in input_paths:
                # Use forward slashes for FFmpeg compatibility
                safe_path = path.replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        ]
        logger.info("Concat command: %s", " ".join(cmd))
        return cmd

    def concat_with_transition(
        self,
        input_paths: list[str],
        output_path: str,
        transition: str = "fade",
        transition_duration: float = 1.0,
    ) -> list[str]:
        """Concatenate videos with xfade transitions (requires re-encoding)."""
        if len(input_paths) < 2:
            raise FFmpegError("Need at least 2 videos for transitions")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Build the filter_complex for xfade chain
        # For N inputs: N-1 xfade filters chained together
        inputs = []
        for path in input_paths:
            inputs.extend(["-i", path])

        # Get durations for offset calculation
        durations = []
        for path in input_paths:
            meta = self.probe(path)
            durations.append(meta["duration"])

        filter_parts = []
        current_label = "[0:v]"

        for i in range(1, len(input_paths)):
            # Calculate offset: sum of previous durations minus accumulated transition time
            offset = sum(durations[:i]) - transition_duration * i
            offset = max(0, round(offset, 2))

            next_input = f"[{i}:v]"
            out_label = f"[v{i}]" if i < len(input_paths) - 1 else "[vout]"

            filter_parts.append(
                f"{current_label}{next_input}xfade=transition={transition}"
                f":duration={transition_duration}:offset={offset}{out_label}"
            )
            current_label = out_label

        filter_complex = ";".join(filter_parts)

        cmd = [
            self.ffmpeg_path,
            "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            output_path,
        ]
        logger.info("Transition command: %s", " ".join(cmd))
        return cmd

    def change_speed(
        self,
        input_path: str,
        output_path: str,
        speed_factor: float,
    ) -> list[str]:
        """Change video playback speed."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        video_filter = f"setpts={1/speed_factor}*PTS"
        audio_filter = f"atempo={speed_factor}"

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-filter:v", video_filter,
            "-filter:a", audio_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            output_path,
        ]
        logger.info("Speed command: %s", " ".join(cmd))
        return cmd

    def reframe(
        self,
        input_path: str,
        output_path: str,
        target: str = "shorts",
    ) -> list[str]:
        """Reframe video for different platforms via center-crop + scale.

        target options: 'shorts' | 'reels' | 'tiktok' (9:16, 1080x1920)
                        'youtube' (16:9, 1920x1080)
                        'square' (1:1, 1080x1080)
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        presets = {
            "shorts":  ("crop=ih*9/16:ih", "scale=1080:1920"),
            "reels":   ("crop=ih*9/16:ih", "scale=1080:1920"),
            "tiktok":  ("crop=ih*9/16:ih", "scale=1080:1920"),
            "youtube": ("crop=iw:iw*9/16", "scale=1920:1080"),
            "square":  ("crop=min(iw\\,ih):min(iw\\,ih)", "scale=1080:1080"),
        }
        crop, scale = presets.get(target.lower(), presets["shorts"])
        vf = f"{crop},{scale}"

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", input_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            output_path,
        ]
        logger.info("Reframe command (%s): %s", target, " ".join(cmd))
        return cmd

    def detect_silence(
        self,
        input_path: str,
        noise_db: float = -35.0,
        min_duration: float = 0.5,
    ) -> list[tuple[float, float]]:
        """Run silencedetect and return list of (silence_start, silence_end) tuples."""
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", input_path,
            "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
            "-f", "null", "-",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr
        silences: list[tuple[float, float]] = []
        starts: list[float] = []
        for line in output.splitlines():
            if "silence_start" in line:
                try:
                    starts.append(float(line.split("silence_start:")[1].strip()))
                except (IndexError, ValueError):
                    pass
            elif "silence_end" in line:
                try:
                    end = float(line.split("silence_end:")[1].split("|")[0].strip())
                    if starts:
                        silences.append((starts.pop(0), end))
                except (IndexError, ValueError):
                    pass
        return silences

    def remove_silence(
        self,
        input_path: str,
        output_path: str,
        noise_db: float = -35.0,
        min_duration: float = 0.5,
    ) -> list[str]:
        """Build FFmpeg command to remove silent segments."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        audio_filter = (
            f"silenceremove=start_periods=1:start_duration={min_duration}"
            f":start_threshold={noise_db}dB"
            f":stop_periods=-1:stop_duration={min_duration}"
            f":stop_threshold={noise_db}dB"
        )
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", input_path,
            "-af", audio_filter,
            "-c:v", "copy",
            output_path,
        ]
        logger.info("Remove silence command: %s", " ".join(cmd))
        return cmd

    def generate_subtitles(
        self,
        input_path: str,
        srt_path: str,
        api_key: str,
        language: str = "en",
    ) -> str:
        """Transcribe audio with OpenAI Whisper API and write .srt file."""
        import os
        import tempfile
        try:
            from openai import OpenAI
        except ImportError:
            raise FFmpegError("openai package not installed. Run: pip install openai")

        audio_tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        audio_tmp.close()
        extract_cmd = [
            self.ffmpeg_path, "-y",
            "-i", input_path,
            "-vn", "-acodec", "libmp3lame", "-q:a", "4",
            audio_tmp.name,
        ]
        result = subprocess.run(extract_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFmpegError(f"Audio extraction failed: {result.stderr[-300:]}")

        client = OpenAI(api_key=api_key)
        with open(audio_tmp.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="srt",
                language=language,
            )

        Path(srt_path).parent.mkdir(parents=True, exist_ok=True)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        os.unlink(audio_tmp.name)
        logger.info("Subtitles written to %s", srt_path)
        return srt_path

    def burn_subtitles(
        self,
        input_path: str,
        srt_path: str,
        output_path: str,
    ) -> list[str]:
        """Burn .srt subtitles into video."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        safe_srt = srt_path.replace("\\", "/").replace(":", "\\:")
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", input_path,
            "-vf", f"subtitles='{safe_srt}'",
            "-c:a", "copy",
            output_path,
        ]
        logger.info("Burn subtitles command: %s", " ".join(cmd))
        return cmd

    def execute(self, command: list[str], timeout: int = 300) -> dict:
        """Execute an FFmpeg command and return result."""
        logger.info("Executing: %s", " ".join(command[:6]) + " ...")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            success = result.returncode == 0

            if not success:
                logger.error("FFmpeg failed: %s", result.stderr[-500:])
            else:
                logger.info("FFmpeg command completed successfully")

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": success,
            }
        except subprocess.TimeoutExpired:
            raise FFmpegError(f"FFmpeg command timed out after {timeout}s")
        except FileNotFoundError:
            raise FFmpegError(
                f"FFmpeg not found at '{self.ffmpeg_path}'. "
                "Please install FFmpeg and add it to PATH."
            )
