from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import Settings
from core.ffmpeg_builder import FFmpegBuilder

PLATFORM_PRESETS = {
    "youtube":  {"label": "YouTube (16:9)",        "width": 1920, "height": 1080, "ratio": "16:9"},
    "shorts":   {"label": "YouTube Shorts (9:16)", "width": 1080, "height": 1920, "ratio": "9:16"},
    "reels":    {"label": "Instagram Reels (9:16)","width": 1080, "height": 1920, "ratio": "9:16"},
    "tiktok":   {"label": "TikTok (9:16)",         "width": 1080, "height": 1920, "ratio": "9:16"},
    "square":   {"label": "Instagram Square (1:1)","width": 1080, "height": 1080, "ratio": "1:1"},
    "original": {"label": "Keep Original",         "width": 0,    "height": 0,    "ratio": "original"},
}


class ReframeVideoInput(BaseModel):
    input_path: str = Field(description="Path to the input video file")
    output_path: str = Field(description="Path for the reframed output video")
    platform: str = Field(
        default="shorts",
        description=(
            "Target platform: 'youtube' (16:9 1920x1080), 'shorts' (9:16 1080x1920), "
            "'reels' (9:16 1080x1920), 'tiktok' (9:16 1080x1920), 'square' (1:1 1080x1080), "
            "'original' (keep aspect ratio)."
        ),
    )


class ReframeVideoTool(BaseTool):
    name: str = "reframe_video"
    description: str = (
        "Converts a video to the target platform's aspect ratio using center-crop. "
        "Use 'shorts'/'reels'/'tiktok' for vertical 9:16, 'youtube' for horizontal 16:9, "
        "'square' for 1:1. Returns the path to the reframed video on success."
    )
    args_schema: Type[BaseModel] = ReframeVideoInput

    def _run(self, input_path: str, output_path: str, platform: str = "shorts") -> str:
        if platform.lower() == "original":
            import shutil
            shutil.copy2(input_path, output_path)
            return f"Kept original aspect ratio, copied to: {output_path}"

        settings = Settings()
        builder = FFmpegBuilder(settings.ffmpeg_path)
        cmd = builder.reframe(input_path, output_path, platform)
        result = builder.execute(cmd, timeout=600)
        if result["success"]:
            preset = PLATFORM_PRESETS.get(platform.lower(), {})
            return (
                f"Reframed for {preset.get('label', platform)} "
                f"({preset.get('ratio', '')}): {output_path}"
            )
        return f"Error reframing video: {result['stderr'][-300:]}"
