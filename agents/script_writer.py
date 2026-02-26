from crewai import Agent, LLM

from config.prompts import SCRIPT_WRITER_BACKSTORY


def create_script_writer_agent(llm: LLM) -> Agent:
    """Create the Script Writer agent that plans edits."""
    return Agent(
        role="Video Edit Planner",
        goal=(
            "Transform content analysis and user instructions into a precise, "
            "structured editing plan with specific timestamps, transitions, "
            "and operation sequences that can be executed by FFmpeg. "
            "Output a JSON plan only — do not call any tools."
        ),
        backstory=SCRIPT_WRITER_BACKSTORY,
        llm=llm,
        tools=[],
        allow_delegation=False,
        verbose=True,
        max_iter=3,
    )
