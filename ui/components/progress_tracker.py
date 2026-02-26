from __future__ import annotations

import streamlit as st

from models.enums import PipelineStage

STAGE_LABELS = {
    PipelineStage.UPLOAD: "Preparing video...",
    PipelineStage.FRAME_EXTRACTION: "Extracting frames...",
    PipelineStage.SCENE_DETECTION: "Detecting scenes...",
    PipelineStage.CONTENT_ANALYSIS: "AI analyzing content (Moondream)...",
    PipelineStage.EDIT_PLANNING: "Planning edits (GPT-4)...",
    PipelineStage.COMMAND_GENERATION: "Generating FFmpeg commands...",
    PipelineStage.EXECUTION: "Executing edits...",
    PipelineStage.DELIVERY: "Preparing final video...",
}


def render_progress(state) -> None:
    """Render real-time pipeline progress."""
    if state is None:
        return

    # Progress bar
    progress = state.progress_percent / 100.0
    st.progress(progress)

    # Current stage label
    stage_label = STAGE_LABELS.get(state.current_stage, "Working...")
    st.markdown(f"**{stage_label}**")

    # Agent activity log
    if state.logs:
        with st.expander("Agent Activity Log", expanded=True):
            for log_entry in state.logs:
                st.text(log_entry)
