from crewai import Agent, LLM

from config.prompts import CONTENT_ANALYZER_BACKSTORY
from tools.frame_extraction import ExtractFramesTool
from tools.scene_detection import DetectScenesTool
from tools.vision_analysis import AnalyzeFrameTool


def create_content_analyzer_agent(
    llm: LLM,
    video_path: str = "",
    temp_dir: str = "",
) -> Agent:
    """Create the Content Analyzer agent.

    Uses a local Ollama LLM for reasoning and
    Ollama vision model for frame analysis.
    """
    return Agent(
        role="Video Content Analyst",
        goal=(
            "Analyze video content by extracting frames, detecting scene "
            "boundaries, and providing detailed descriptions of visual content "
            "to inform editing decisions."
        ),
        backstory=CONTENT_ANALYZER_BACKSTORY,
        llm=llm,
        tools=[
            ExtractFramesTool(video_path=video_path, output_dir=temp_dir),
            DetectScenesTool(video_path=video_path),
            AnalyzeFrameTool(),
        ],
        allow_delegation=False,
        verbose=True,
        max_iter=10,
    )
