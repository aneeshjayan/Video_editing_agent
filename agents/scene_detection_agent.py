from crewai import Agent, LLM

from tools.frame_extraction import ExtractFramesTool
from tools.scene_detection import DetectScenesTool
from tools.vision_analysis import AnalyzeFrameTool


def create_scene_detection_agent(llm: LLM, video_path: str = "", temp_dir: str = "") -> Agent:
    return Agent(
        role="Scene Detection Specialist",
        goal=(
            "Detect all scene boundaries in the video, extract representative frames, "
            "and describe the visual content of each scene with timestamps. "
            "Provide a structured scene map that the narrative structurer can use."
        ),
        backstory=(
            "You are a cinematography expert who analyzes video frame-by-frame to find "
            "natural scene cuts, shot changes, and visual transitions. You describe what "
            "happens in each scene — who is on screen, what action is occurring, the "
            "setting and mood — so editors can make intelligent decisions about structure."
        ),
        llm=llm,
        tools=[
            DetectScenesTool(video_path=video_path),
            ExtractFramesTool(video_path=video_path, output_dir=temp_dir),
            AnalyzeFrameTool(),
        ],
        allow_delegation=False,
        verbose=True,
        max_iter=10,
    )
