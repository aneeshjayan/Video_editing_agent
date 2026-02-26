from __future__ import annotations

from pydantic import BaseModel, Field

from models.enums import TransitionType, EditOperation


class VideoMetadata(BaseModel):
    file_path: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    codec: str
    file_size_bytes: int


class SceneInfo(BaseModel):
    scene_index: int
    start_time: float
    end_time: float
    duration: float
    description: str
    thumbnail_path: str | None = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class EditStep(BaseModel):
    operation: EditOperation
    start_time: float | None = None
    end_time: float | None = None
    transition_type: TransitionType | None = None
    transition_duration: float | None = None
    speed_factor: float | None = None
    description: str


class EditPlan(BaseModel):
    original_video: VideoMetadata
    steps: list[EditStep]
    expected_output_duration: float | None = None
    ffmpeg_commands: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    scenes: list[SceneInfo]
    total_scenes: int
    key_moments: list[str]
    overall_description: str
    suggested_highlights: list[tuple[float, float]] = Field(default_factory=list)
