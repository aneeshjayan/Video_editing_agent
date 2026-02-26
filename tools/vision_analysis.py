from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool
from PIL import Image
from pydantic import BaseModel, Field

from config.settings import Settings
from services.vision_service import create_vision_service


class AnalyzeFrameInput(BaseModel):
    frame_path: str = Field(description="Path to the frame image file")
    question: str = Field(
        default="",
        description=(
            "Optional question about the frame. If empty, generates a general caption. "
            "Example: 'Are there people in this scene?' or 'What action is happening?'"
        ),
    )


class AnalyzeFrameTool(BaseTool):
    name: str = "analyze_video_frame"
    description: str = (
        "Analyzes a single video frame using the Moondream vision AI model. "
        "Can generate a description of the frame or answer a specific question "
        "about what's visible in the image. Use this after extracting frames "
        "to understand video content."
    )
    args_schema: Type[BaseModel] = AnalyzeFrameInput

    def _run(self, frame_path: str, question: str = "") -> str:
        settings = Settings()
        vision = create_vision_service(settings)
        image = Image.open(frame_path)

        if question:
            answer = vision.query(image, question)
            return f"Q: {question}\nA: {answer}"
        else:
            caption = vision.caption(image)
            return f"Frame description: {caption}"
