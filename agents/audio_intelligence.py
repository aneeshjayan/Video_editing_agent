from crewai import Agent, LLM

from tools.audio_tools import DetectFillerWordsTool, TranscribeAudioTool
from tools.ffmpeg_tools import ProbeVideoTool, RemoveSilenceTool


def create_audio_intelligence_agent(llm: LLM) -> Agent:
    return Agent(
        role="Audio Intelligence Specialist",
        goal=(
            "Analyze video audio to produce a precise transcript with timestamps, "
            "identify filler words (um, uh, like, you know), detect silent gaps, "
            "and provide a clean audio analysis report for the editing pipeline."
        ),
        backstory=(
            "You are an audio engineer and linguist who specializes in speech analysis. "
            "You use AI transcription to find every word and timestamp, then identify "
            "filler words, long pauses, and awkward speech patterns that should be removed "
            "to make the video crisp and professional. Your analysis directly feeds the "
            "clip trimmer, so precision is critical."
        ),
        llm=llm,
        tools=[
            TranscribeAudioTool(),
            DetectFillerWordsTool(),
            RemoveSilenceTool(),
            ProbeVideoTool(),
        ],
        allow_delegation=False,
        verbose=True,
        max_iter=8,
    )
