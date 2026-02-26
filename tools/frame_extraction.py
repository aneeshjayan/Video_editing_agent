from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config.settings import Settings
from core.frame_extractor import FrameExtractor


class ExtractFramesInput(BaseModel):
    interval_seconds: float = Field(
        default=1.0,
        description="Extract one frame every N seconds",
    )
    max_frames: int = Field(
        default=60,
        description="Maximum number of frames to extract",
    )


class ExtractFramesTool(BaseTool):
    name: str = "extract_frames"
    description: str = (
        "Extracts representative frames from the video at regular intervals. "
        "Returns a list of extracted frame file paths with their timestamps. "
        "The video path and output directory are already configured — just call this tool."
    )
    args_schema: Type[BaseModel] = ExtractFramesInput
    video_path: str = ""
    output_dir: str = ""

    def _run(
        self,
        interval_seconds: float = 1.0,
        max_frames: int = 60,
    ) -> str:
        interval_seconds = float(interval_seconds)
        max_frames = int(max_frames)
        extractor = FrameExtractor(interval_seconds=interval_seconds)
        frames = extractor.extract_frames(self.video_path, self.output_dir, max_frames)

        # Return frame info without PIL images (not serializable)
        frame_info = [
            {"path": f["path"], "timestamp": f["timestamp"]}
            for f in frames
        ]
        return json.dumps({
            "total_frames": len(frame_info),
            "frames": frame_info,
        }, indent=2)
