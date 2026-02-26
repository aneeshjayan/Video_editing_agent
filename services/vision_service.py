from __future__ import annotations

import base64
import io
from abc import ABC, abstractmethod

import requests
from PIL import Image

from config.logging_config import logger
from core.exceptions import VisionServiceError


class VisionService(ABC):
    """Abstract base for vision model services."""

    @abstractmethod
    def caption(self, image: Image.Image) -> str:
        """Generate a text caption describing the image."""

    @abstractmethod
    def query(self, image: Image.Image, question: str) -> str:
        """Answer a question about the image content."""


class OllamaVisionService(VisionService):
    """Local Ollama vision model (e.g. llama3.2-vision) — no API key needed."""

    def __init__(self, model: str = "llama3.2-vision", base_url: str = "http://localhost:11434"):
        self.model = model
        self.api_url = f"{base_url.rstrip('/')}/api/generate"

    def _image_to_base64(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _call(self, image: Image.Image, prompt: str) -> str:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [self._image_to_base64(image)],
                "stream": False,
            }
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise VisionServiceError(
                f"Cannot connect to Ollama at {self.api_url}. "
                "Make sure Ollama is running: open a terminal and run 'ollama serve'"
            )
        except Exception as e:
            raise VisionServiceError(f"Ollama vision call failed: {e}") from e

    def caption(self, image: Image.Image) -> str:
        return self._call(image, "Describe what you see in this video frame in detail.")

    def query(self, image: Image.Image, question: str) -> str:
        return self._call(image, question)


class OpenAIVisionService(VisionService):
    """OpenAI GPT-4o vision — fast and accurate, requires API key."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise VisionServiceError("openai package not installed. Run: pip install openai")
        self.model = model

    def _image_to_base64(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _call(self, image: Image.Image, prompt: str) -> str:
        try:
            b64 = self._image_to_base64(image)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }],
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise VisionServiceError(f"OpenAI vision call failed: {e}") from e

    def caption(self, image: Image.Image) -> str:
        return self._call(image, "Describe what you see in this video frame in 2-3 sentences. Focus on people, actions, setting, and mood.")

    def query(self, image: Image.Image, question: str) -> str:
        return self._call(image, question)


def create_vision_service(settings) -> VisionService:
    """Factory: returns OpenAI vision if API key is set, else Ollama."""
    if settings.use_openai:
        logger.info("Using OpenAI vision model '%s'", settings.openai_vision_model)
        return OpenAIVisionService(
            api_key=settings.openai_api_key,
            model=settings.openai_vision_model,
        )
    model = settings.ollama_vision_model
    base_url = settings.ollama_base_url
    logger.info("Using Ollama vision model '%s' at %s", model, base_url)
    return OllamaVisionService(model=model, base_url=base_url)
