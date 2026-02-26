from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# Always resolve .env relative to this file's parent (the project root)
_ENV_FILE = str(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    # OpenAI - for LLM reasoning and vision (recommended for speed)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_vision_model: str = Field(default="gpt-4o", alias="OPENAI_VISION_MODEL")

    # Ollama - fallback local option (used if openai_api_key is empty)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")
    ollama_vision_model: str = Field(default="llama3.2-vision", alias="OLLAMA_VISION_MODEL")

    # Video Processing
    max_video_size_mb: int = Field(default=500, alias="MAX_VIDEO_SIZE_MB")
    frame_extraction_interval: float = Field(default=5.0, alias="FRAME_EXTRACTION_INTERVAL")
    temp_dir: str = Field(default="./tmp", alias="TEMP_DIR")
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")

    @property
    def use_openai(self) -> bool:
        return bool(self.openai_api_key)

    model_config = {
        "env_file": _ENV_FILE,
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }
