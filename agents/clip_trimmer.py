from crewai import Agent, LLM

from tools.ffmpeg_tools import (
    ConcatVideosTool,
    ProbeVideoTool,
    RemoveSilenceTool,
    TrimVideoTool,
)


def create_clip_trimmer_agent(llm: LLM) -> Agent:
    return Agent(
        role="Clip Trimming Specialist",
        goal=(
            "Using the audio analysis and scene map, cut the video into clean segments "
            "by removing silence, filler words, mistakes, and unwanted sections. "
            "Produce a trimmed, concatenated video ready for narrative structuring."
        ),
        backstory=(
            "You are a professional video editor who executes precise cuts. You take "
            "the audio intelligence report (silence timestamps, filler timestamps) and "
            "the scene analysis, then use FFmpeg tools to trim out every unwanted moment. "
            "You always verify each output with probe_video before proceeding and "
            "concatenate clean segments into a single polished clip."
        ),
        llm=llm,
        tools=[
            TrimVideoTool(),
            ConcatVideosTool(),
            RemoveSilenceTool(),
            ProbeVideoTool(),
        ],
        allow_delegation=False,
        verbose=True,
        max_iter=15,
    )
