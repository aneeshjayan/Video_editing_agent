from __future__ import annotations

from pathlib import Path

import cv2
from PIL import Image

from config.logging_config import logger
from core.exceptions import FrameExtractionError


class FrameExtractor:
    """Extracts representative frames from a video at regular intervals."""

    def __init__(self, interval_seconds: float = 1.0):
        self.interval = interval_seconds

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        max_frames: int = 60,
    ) -> list[dict]:
        """Extract frames from video at regular intervals.

        Returns list of dicts with keys: path, timestamp, frame_number, pil_image.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FrameExtractionError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            raise FrameExtractionError(f"Invalid FPS ({fps}) for video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(fps * self.interval))

        logger.info(
            "Extracting frames: fps=%.1f, total=%d, interval=%d frames (%.1fs)",
            fps, total_frames, frame_interval, self.interval,
        )

        frames: list[dict] = []
        frame_count = 0
        extracted = 0

        try:
            while cap.isOpened() and extracted < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    timestamp = frame_count / fps
                    frame_filename = f"frame_{extracted:04d}.jpg"
                    frame_path = output_path / frame_filename

                    cv2.imwrite(str(frame_path), frame)

                    pil_image = Image.fromarray(
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    )

                    frames.append({
                        "path": str(frame_path),
                        "timestamp": round(timestamp, 2),
                        "frame_number": frame_count,
                        "pil_image": pil_image,
                    })
                    extracted += 1

                frame_count += 1
        finally:
            cap.release()

        logger.info("Extracted %d frames from %s", len(frames), video_path)
        return frames

    def extract_single_frame(
        self,
        video_path: str,
        timestamp: float,
        output_path: str,
    ) -> dict:
        """Extract a single frame at a specific timestamp."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FrameExtractionError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        target_frame = int(timestamp * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise FrameExtractionError(
                f"Cannot read frame at timestamp {timestamp}s (frame {target_frame})"
            )

        cv2.imwrite(output_path, frame)
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        return {
            "path": output_path,
            "timestamp": timestamp,
            "frame_number": target_frame,
            "pil_image": pil_image,
        }
