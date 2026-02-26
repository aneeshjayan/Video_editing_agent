from crewai import Agent, LLM

from config.prompts import EXECUTOR_BACKSTORY
from tools.ffmpeg_tools import (
    AddTransitionTool,
    ChangeSpeedTool,
    ConcatVideosTool,
    GenerateSubtitlesTool,
    ProbeVideoTool,
    RemoveSilenceTool,
    TrimVideoTool,
)


def create_executor_agent(llm: LLM) -> Agent:
    """Create the Executor agent that runs FFmpeg commands."""
    return Agent(
        role="FFmpeg Execution Specialist",
        goal=(
            "Execute video editing operations by running the appropriate tools "
            "based on the edit plan. Verify each operation produces valid output "
            "using probe_video before proceeding. Save the final result locally."
        ),
        backstory=EXECUTOR_BACKSTORY,
        llm=llm,
        tools=[
            TrimVideoTool(),
            ConcatVideosTool(),
            AddTransitionTool(),
            ChangeSpeedTool(),
            RemoveSilenceTool(),
            GenerateSubtitlesTool(),
            ProbeVideoTool(),
        ],
        allow_delegation=False,
        verbose=True,
        max_iter=15,
    )
