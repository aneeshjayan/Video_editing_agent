from crewai import Agent, LLM

from config.prompts import ORCHESTRATOR_BACKSTORY


def create_orchestrator_agent(llm: LLM) -> Agent:
    """Create the Orchestrator agent that manages the editing pipeline."""
    return Agent(
        role="Video Editing Orchestrator",
        goal=(
            "Receive user video editing requests, break them into actionable "
            "subtasks, delegate to specialist agents, and ensure the final "
            "edited video matches the user's creative intent."
        ),
        backstory=ORCHESTRATOR_BACKSTORY,
        llm=llm,
        allow_delegation=True,
        verbose=True,
        max_iter=15,
        memory=True,
    )
