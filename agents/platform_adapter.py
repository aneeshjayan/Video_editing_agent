from crewai import Agent, LLM

from tools.ffmpeg_tools import ChangeSpeedTool, ConcatVideosTool, GenerateSubtitlesTool, ProbeVideoTool
from tools.platform_tools import ReframeVideoTool


def create_platform_adapter_agent(llm: LLM) -> Agent:
    return Agent(
        role="Platform Adaptation Specialist",
        goal=(
            "Take the edited video and adapt it for the target platform: reframe the "
            "aspect ratio, add subtitles/captions if requested, adjust pacing, and "
            "produce the final output.mp4 optimized for the target format."
        ),
        backstory=(
            "You are a social media video specialist who knows every platform's "
            "technical requirements. You convert videos between aspect ratios using "
            "smart center-crop, add burnt-in captions for silent autoplay viewing, "
            "and fine-tune pacing so content hits the right beats for each platform. "
            "You always save the final output as output.mp4 in the job temp directory."
        ),
        llm=llm,
        tools=[
            ReframeVideoTool(),
            GenerateSubtitlesTool(),
            ChangeSpeedTool(),
            ConcatVideosTool(),
            ProbeVideoTool(),
        ],
        allow_delegation=False,
        verbose=True,
        max_iter=10,
    )
