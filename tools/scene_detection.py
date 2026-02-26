from __future__ import annotations

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from core.scene_detector import SceneDetector


class DetectScenesInput(BaseModel):
    threshold: float = Field(
        default=0.4,
        description=(
            "Scene change sensitivity (0.0-1.0). Lower = more sensitive "
            "(detects subtle changes), higher = less sensitive. Default 0.4."
        ),
    )


class DetectScenesTool(BaseTool):
    name: str = "detect_scenes"
    description: str = (
        "Analyzes the video to detect scene boundaries using visual histogram comparison. "
        "Returns a list of scenes with start/end timestamps. "
        "The video path is already configured — just call this tool with an optional threshold."
    )
    args_schema: Type[BaseModel] = DetectScenesInput
    video_path: str = ""

    def _run(self, threshold: float = 0.4) -> str:
        threshold = float(threshold)
        detector = SceneDetector(threshold=threshold)
        scenes = detector.detect_scenes_histogram(self.video_path)

        scene_list = [
            {
                "scene_index": i,
                "start_time": start,
                "end_time": end,
                "duration": round(end - start, 2),
            }
            for i, (start, end) in enumerate(scenes)
        ]
        return json.dumps({
            "total_scenes": len(scene_list),
            "scenes": scene_list,
        }, indent=2)
