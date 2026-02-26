from __future__ import annotations

from pathlib import Path

import streamlit as st


def render_preview(output_path: str | None = None) -> None:
    """Render the output video preview with download option."""
    if output_path and Path(output_path).exists():
        st.markdown("**Edited Video**")
        st.video(output_path)

        # Download button
        with open(output_path, "rb") as f:
            video_bytes = f.read()

        st.download_button(
            label="⬇️ Download Edited Video",
            data=video_bytes,
            file_name=Path(output_path).name,
            mime="video/mp4",
        )

        st.caption(f"Saved locally: `{output_path}`")
    else:
        st.info("Edited video will appear here after processing.")
