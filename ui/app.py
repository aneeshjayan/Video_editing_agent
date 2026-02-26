"""AI Video Editor — Streamlit Application.

6-agent AI video editing: Orchestrator, Audio Intelligence, Scene Detection,
Clip Trimmer, Narrative Structurer, Platform Adapter.
Run with: streamlit run ui/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

from agents.flow import VideoEditFlow
from tools.platform_tools import PLATFORM_PRESETS
from ui.components.edit_interface import render_edit_interface
from ui.components.progress_tracker import render_progress
from ui.components.video_preview import render_preview
from ui.components.video_upload import render_upload_section

st.set_page_config(
    page_title="AI Video Editor",
    page_icon="\U0001F3AC",
    layout="wide",
)

Path("./tmp").mkdir(exist_ok=True)


def init_session_state():
    defaults = {
        "pipeline_state": None,
        "is_processing": False,
        "edit_instruction": "",
        "platform": "original",
        "add_subtitles": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def run_pipeline(video_paths: list[str], instruction: str, platform: str, add_subtitles: bool):
    st.session_state["is_processing"] = True
    flow = VideoEditFlow()

    def on_progress(state):
        st.session_state["pipeline_state"] = state

    result = flow.run(
        video_paths=video_paths,
        user_instruction=instruction,
        platform=platform,
        add_subtitles=add_subtitles,
        progress_callback=on_progress,
    )
    st.session_state["pipeline_state"] = result
    st.session_state["is_processing"] = False


def main():
    init_session_state()

    st.title("\U0001F3AC AI Video Editor")
    st.caption(
        "6-agent AI pipeline: Audio Intelligence · Scene Detection · Clip Trimming · "
        "Narrative Structuring · Platform Adaptation — powered by OpenAI + CrewAI + FFmpeg."
    )
    st.divider()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Agent Pipeline")
        st.markdown(
            "**Simple edits** (trim, speed, silence):\n"
            "- Script Writer → Executor\n\n"
            "**Smart edits** (highlights, best moments):\n"
            "- Analyzer → Script Writer → Executor\n\n"
            "**Full pipeline** (Shorts/Reels/TikTok, filler removal):\n"
            "1. Orchestrator\n"
            "2. Audio Intelligence\n"
            "3. Scene Detection\n"
            "4. Clip Trimmer\n"
            "5. Narrative Structurer\n"
            "6. Platform Adapter"
        )
        st.divider()
        st.markdown("**Stack:** OpenAI GPT-4o · Whisper · CrewAI · FFmpeg · OpenCV")

        state = st.session_state.get("pipeline_state")
        if state:
            st.divider()
            st.subheader("Pipeline Status")
            icons = {"pending": "🟡", "in_progress": "🔵", "completed": "🟢", "failed": "🔴"}
            icon = icons.get(str(state.status), "")
            st.markdown(f"{icon} **{str(state.status).upper()}**")
            st.markdown(f"Job: `{state.job_id}`")
            if state.logs:
                with st.expander("Logs", expanded=False):
                    for log in state.logs[-15:]:
                        st.text(log)

    # ── Main Layout ───────────────────────────────────────────────────────────
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("Input")

        video_paths = render_upload_section()

        if video_paths:
            st.divider()

            # Platform selector
            st.markdown("**Target Platform**")
            platform_options = {v["label"]: k for k, v in PLATFORM_PRESETS.items()}
            selected_label = st.selectbox(
                "Platform",
                options=list(platform_options.keys()),
                index=list(platform_options.keys()).index("Keep Original"),
                label_visibility="collapsed",
            )
            platform = platform_options[selected_label]
            st.session_state["platform"] = platform

            # Subtitles toggle
            add_subtitles = st.toggle(
                "Auto-generate subtitles (Whisper)",
                value=st.session_state.get("add_subtitles", False),
            )
            st.session_state["add_subtitles"] = add_subtitles

            st.divider()

            # Edit instruction
            instruction = render_edit_interface()

            # Run button
            if instruction and not st.session_state["is_processing"]:
                if st.button(
                    "\U0001F680 Edit Video",
                    type="primary",
                    use_container_width=True,
                ):
                    run_pipeline(video_paths, instruction, platform, add_subtitles)
                    st.rerun()
            elif st.session_state["is_processing"]:
                st.warning("Processing... please wait.")

        state = st.session_state.get("pipeline_state")
        if state:
            st.divider()
            render_progress(state)

    with col_output:
        st.subheader("Output")

        state = st.session_state.get("pipeline_state")

        if state and str(state.status) == "completed":
            render_preview(output_path=state.output_path)

            # AI Edit Explanation
            st.divider()
            st.markdown("### What the AI edited")
            if state.edit_explanation:
                st.markdown(state.edit_explanation)
            elif state.crew_output:
                st.info(
                    "OpenAI edit summary unavailable — check that OPENAI_API_KEY is set "
                    "in your .env file and the pipeline completed successfully."
                )
                with st.expander("Raw agent output (fallback)"):
                    st.text(state.crew_output[:3000])
            else:
                st.info("No edit summary available.")

            if state.crew_output and state.edit_explanation:
                with st.expander("Full Agent Output"):
                    st.text(state.crew_output[:3000])

        elif state and str(state.status) == "failed":
            st.error(f"Pipeline failed: {state.error}")
            if state.logs:
                with st.expander("Error Logs"):
                    for log in state.logs:
                        st.text(log)
        else:
            st.info(
                "Upload one or more videos, choose a platform, describe your edit, "
                "and let the agents do the work."
            )


if __name__ == "__main__":
    main()
