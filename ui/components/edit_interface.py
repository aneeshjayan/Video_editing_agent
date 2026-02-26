from __future__ import annotations

import streamlit as st

PRESET_INSTRUCTIONS = {
    "Trim first 10s": "Trim first 10 seconds of the video",
    "Trim last 10s": "Trim last 10 seconds of the video",
    "2x Speed": "Speed up the entire video to 2x speed",
    "Remove Silence": "Remove silence from the video",
    "Add Subtitles": "Add subtitles to the video",
    "30s Highlight": "Create a 30-second highlight reel of the best moments",
    "Add Fades": "Add fade transitions between each detected scene",
    "Keep Best Scenes": "Keep only the most interesting scenes and remove the rest",
}


def render_edit_interface() -> str:
    """Render the edit instruction interface. Returns the user instruction."""
    st.markdown("**What would you like to do?**")

    # Preset buttons in a grid
    cols = st.columns(3)
    selected_preset = None

    for i, (label, instruction) in enumerate(PRESET_INSTRUCTIONS.items()):
        with cols[i % 3]:
            if st.button(label, key=f"preset_{i}", use_container_width=True):
                selected_preset = instruction

    # Store selected preset in session state
    if selected_preset:
        st.session_state["edit_instruction"] = selected_preset

    # Free-form text input
    default_value = st.session_state.get("edit_instruction", "")
    user_input = st.text_area(
        "Or describe your edit in natural language:",
        value=default_value,
        placeholder=(
            "e.g., 'Keep only the scenes with people talking and "
            "add smooth transitions between them'"
        ),
        height=80,
    )

    return user_input
