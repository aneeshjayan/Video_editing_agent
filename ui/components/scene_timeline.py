from __future__ import annotations

from pathlib import Path

import streamlit as st

from models.schemas import SceneInfo


def render_timeline(scenes: list[SceneInfo] | None = None) -> None:
    """Render a visual timeline of detected scenes with thumbnails."""
    if not scenes:
        return

    st.markdown("**Detected Scenes**")

    # Display scenes in rows of 4
    scenes_per_row = 4
    for row_start in range(0, len(scenes), scenes_per_row):
        row_scenes = scenes[row_start : row_start + scenes_per_row]
        cols = st.columns(scenes_per_row)

        for i, scene in enumerate(row_scenes):
            with cols[i]:
                # Show thumbnail if available
                if scene.thumbnail_path and Path(scene.thumbnail_path).exists():
                    st.image(scene.thumbnail_path, use_container_width=True)

                st.caption(
                    f"**Scene {scene.scene_index + 1}**\n"
                    f"{scene.start_time:.1f}s - {scene.end_time:.1f}s\n"
                    f"({scene.duration:.1f}s)"
                )

                # Truncate long descriptions
                desc = scene.description
                if len(desc) > 80:
                    desc = desc[:77] + "..."
                st.text(desc)
