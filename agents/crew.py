from __future__ import annotations

from crewai import Crew, LLM, Process, Task

from agents.audio_intelligence import create_audio_intelligence_agent
from agents.clip_trimmer import create_clip_trimmer_agent
from agents.content_analyzer import create_content_analyzer_agent
from agents.executor import create_executor_agent
from agents.narrative_structurer import create_narrative_structurer_agent
from agents.orchestrator import create_orchestrator_agent
from agents.platform_adapter import create_platform_adapter_agent
from agents.scene_detection_agent import create_scene_detection_agent
from agents.script_writer import create_script_writer_agent
from config.prompts import (
    ANALYZE_TASK_TEMPLATE,
    AUDIO_INTELLIGENCE_TASK_TEMPLATE,
    CLIP_TRIMMING_TASK_TEMPLATE,
    EXECUTE_TASK_TEMPLATE,
    NARRATIVE_STRUCTURE_TASK_TEMPLATE,
    ORCHESTRATE_TASK_TEMPLATE,
    PLAN_TASK_TEMPLATE,
    PLATFORM_ADAPT_TASK_TEMPLATE,
    SCENE_DETECTION_TASK_TEMPLATE,
)
from config.settings import Settings


def _build_llm(settings: Settings) -> LLM:
    """Build the shared LLM — OpenAI if key is set, else Ollama."""
    if settings.use_openai:
        return LLM(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        )
    return LLM(
        model=f"ollama/{settings.ollama_model}",
        base_url=settings.ollama_base_url,
    )


def create_simple_crew(
    video_path: str,
    user_instruction: str,
    video_duration: float,
    video_width: int,
    video_height: int,
    temp_dir: str,
    skip_vision: bool,
) -> Crew:
    """3-agent crew for simple time-based edits (trim, speed, silence, subtitles)."""
    settings = Settings()
    llm = _build_llm(settings)

    writer = create_script_writer_agent(llm)
    executor = create_executor_agent(llm)

    if skip_vision:
        plan_task = Task(
            description=PLAN_TASK_TEMPLATE.format(
                user_instruction=user_instruction,
                duration=video_duration,
                width=video_width,
                height=video_height,
                video_path=video_path,
                temp_dir=temp_dir,
            ),
            expected_output="A JSON edit plan with steps, paths, and timestamps.",
            agent=writer,
        )
        execute_task = Task(
            description=EXECUTE_TASK_TEMPLATE.format(
                temp_dir=temp_dir,
                video_path=video_path,
            ),
            expected_output="Path to the final output.mp4 and a summary.",
            agent=executor,
            context=[plan_task],
        )
        return Crew(
            agents=[writer, executor],
            tasks=[plan_task, execute_task],
            process=Process.sequential,
            verbose=True,
        )

    # With vision analysis
    analyzer = create_content_analyzer_agent(llm, video_path=video_path, temp_dir=temp_dir)
    analyze_task = Task(
        description=ANALYZE_TASK_TEMPLATE.format(
            video_path=video_path,
            user_instruction=user_instruction,
        ),
        expected_output="JSON scene analysis with timestamps, descriptions, and highlights.",
        agent=analyzer,
    )
    plan_task = Task(
        description=PLAN_TASK_TEMPLATE.format(
            user_instruction=user_instruction,
            duration=video_duration,
            width=video_width,
            height=video_height,
            video_path=video_path,
            temp_dir=temp_dir,
        ),
        expected_output="A JSON edit plan with steps, paths, and timestamps.",
        agent=writer,
        context=[analyze_task],
    )
    execute_task = Task(
        description=EXECUTE_TASK_TEMPLATE.format(
            temp_dir=temp_dir,
            video_path=video_path,
        ),
        expected_output="Path to the final output.mp4 and a summary.",
        agent=executor,
        context=[plan_task],
    )
    return Crew(
        agents=[analyzer, writer, executor],
        tasks=[analyze_task, plan_task, execute_task],
        process=Process.sequential,
        verbose=True,
    )


def create_full_crew(
    video_path: str,
    user_instruction: str,
    video_duration: float,
    video_width: int,
    video_height: int,
    temp_dir: str,
    platform: str = "original",
    add_subtitles: bool = False,
    num_videos: int = 1,
) -> Crew:
    """Full 6-agent crew: Orchestrator → Audio → Scene → Trimmer → Narrative → Platform."""
    settings = Settings()
    llm = _build_llm(settings)

    # Build all agents
    orchestrator = create_orchestrator_agent(llm)
    audio_agent = create_audio_intelligence_agent(llm)
    scene_agent = create_scene_detection_agent(llm, video_path=video_path, temp_dir=temp_dir)
    trimmer = create_clip_trimmer_agent(llm)
    narrator = create_narrative_structurer_agent(llm)
    adapter = create_platform_adapter_agent(llm)

    trimmed_video = f"{temp_dir}\\trimmed_final.mp4"

    # Task 1: Orchestrator — master plan
    orchestrate_task = Task(
        description=ORCHESTRATE_TASK_TEMPLATE.format(
            user_instruction=user_instruction,
            platform=platform,
            num_videos=num_videos,
            video_paths=video_path,
            total_duration=video_duration,
            width=video_width,
            height=video_height,
        ),
        expected_output="A JSON master plan with intent, platform, and feature flags.",
        agent=orchestrator,
    )

    # Task 2: Audio Intelligence — transcript + filler detection
    audio_task = Task(
        description=AUDIO_INTELLIGENCE_TASK_TEMPLATE.format(
            video_path=video_path,
            master_plan="{orchestrate_task_output}",
        ),
        expected_output="Audio analysis report: transcript, filler timestamps, silence gaps.",
        agent=audio_agent,
        context=[orchestrate_task],
    )

    # Task 3: Scene Detection — visual scene map
    scene_task = Task(
        description=SCENE_DETECTION_TASK_TEMPLATE.format(
            video_path=video_path,
            temp_dir=temp_dir,
        ),
        expected_output="Scene map with index, timestamps, descriptions, and quality ratings.",
        agent=scene_agent,
        context=[orchestrate_task],
    )

    # Task 4: Clip Trimmer — cuts bad sections
    trim_task = Task(
        description=CLIP_TRIMMING_TASK_TEMPLATE.format(
            video_path=video_path,
            temp_dir=temp_dir,
        ),
        expected_output=f"Path to clean trimmed video at {trimmed_video}.",
        agent=trimmer,
        context=[audio_task, scene_task],
    )

    # Task 5: Narrative Structurer — hook/body/close plan
    narrative_task = Task(
        description=NARRATIVE_STRUCTURE_TASK_TEMPLATE.format(
            user_instruction=user_instruction,
            platform=platform,
            trimmed_video=trimmed_video,
        ),
        expected_output="JSON narrative plan with hook, body segments, closing, and pacing.",
        agent=narrator,
        context=[audio_task, scene_task, trim_task],
    )

    # Task 6: Platform Adapter — reframe + captions + final output
    adapt_task = Task(
        description=PLATFORM_ADAPT_TASK_TEMPLATE.format(
            platform=platform,
            trimmed_video=trimmed_video,
            temp_dir=temp_dir,
            add_subtitles=str(add_subtitles).lower(),
        ),
        expected_output=f"Final output.mp4 at {temp_dir}\\output.mp4 ready for {platform}.",
        agent=adapter,
        context=[narrative_task, trim_task],
    )

    return Crew(
        agents=[orchestrator, audio_agent, scene_agent, trimmer, narrator, adapter],
        tasks=[orchestrate_task, audio_task, scene_task, trim_task, narrative_task, adapt_task],
        process=Process.sequential,
        verbose=True,
    )


def create_video_editing_crew(
    video_path: str,
    user_instruction: str,
    video_duration: float = 0.0,
    video_width: int = 0,
    video_height: int = 0,
    temp_dir: str = "./tmp",
    skip_vision: bool = False,
    use_full_pipeline: bool = False,
    platform: str = "original",
    add_subtitles: bool = False,
    num_videos: int = 1,
) -> Crew:
    """Entry point — routes to simple 3-agent or full 6-agent crew."""
    if use_full_pipeline:
        return create_full_crew(
            video_path=video_path,
            user_instruction=user_instruction,
            video_duration=video_duration,
            video_width=video_width,
            video_height=video_height,
            temp_dir=temp_dir,
            platform=platform,
            add_subtitles=add_subtitles,
            num_videos=num_videos,
        )
    return create_simple_crew(
        video_path=video_path,
        user_instruction=user_instruction,
        video_duration=video_duration,
        video_width=video_width,
        video_height=video_height,
        temp_dir=temp_dir,
        skip_vision=skip_vision,
    )
