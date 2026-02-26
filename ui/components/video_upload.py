from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st


def render_upload_section() -> list[str]:
    """Render multi-video upload widget. Returns list of absolute temp file paths."""
    uploaded_files = st.file_uploader(
        "Upload video(s)",
        type=["mp4", "mov", "avi", "mkv"],
        accept_multiple_files=True,
        help="Upload one or more videos. Multiple videos will be merged before editing.",
    )

    if not uploaded_files:
        return []

    paths = []
    total_mb = 0.0

    for uploaded in uploaded_files:
        suffix = Path(uploaded.name).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir="./tmp")
        tmp.write(uploaded.read())
        tmp.flush()
        tmp.close()
        paths.append(str(Path(tmp.name).resolve()))
        total_mb += uploaded.size / (1024 * 1024)

    # Preview first video
    st.video(uploaded_files[0])

    if len(uploaded_files) == 1:
        st.caption(f"{uploaded_files[0].name} | {total_mb:.1f} MB")
    else:
        names = ", ".join(f.name for f in uploaded_files)
        st.caption(f"{len(uploaded_files)} videos: {names} | {total_mb:.1f} MB total")
        st.info("Videos will be merged in the order listed above before editing.")

    return paths
