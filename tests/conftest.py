import os
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temp directory for test outputs."""
    return str(tmp_path)


@pytest.fixture
def sample_video_path():
    """Path to a sample test video (must exist for integration tests)."""
    path = Path(__file__).parent / "fixtures" / "sample_short.mp4"
    return str(path)


@pytest.fixture
def mock_settings():
    """Return a Settings-like object with test values."""

    class MockSettings:
        openrouter_api_key = "test-openrouter-key"
        openrouter_model = "meta-llama/llama-3.3-70b-instruct:free"
        openrouter_api_base = "https://openrouter.ai/api/v1"
        moondream_api_key = "test-moondream-key"
        moondream_use_local = False
        moondream_local_url = "http://localhost:2020"
        max_video_size_mb = 500
        frame_extraction_interval = 1.0
        temp_dir = "./tmp"
        ffmpeg_path = "ffmpeg"

    return MockSettings()
