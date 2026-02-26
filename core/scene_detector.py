from __future__ import annotations

import cv2
import numpy as np

from config.logging_config import logger
from core.exceptions import SceneDetectionError
from models.schemas import SceneInfo


class SceneDetector:
    """Detects scene boundaries using OpenCV histogram comparison.

    Two-stage approach:
    1. Fast histogram comparison to find boundaries
    2. Optional Vision Model verification to describe each scene
    """

    def __init__(self, threshold: float = 0.4):
        self.threshold = threshold

    def detect_scenes_histogram(self, video_path: str) -> list[tuple[float, float]]:
        """Detect scene boundaries using color histogram comparison.

        Returns list of (start_time, end_time) tuples for each scene.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise SceneDetectionError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            raise SceneDetectionError(f"Invalid FPS for video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Sample every 5th frame for speed
        sample_interval = max(1, int(fps / 5))

        prev_hist = None
        scene_boundaries = [0.0]
        frame_idx = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_interval == 0:
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    hist = cv2.calcHist(
                        [hsv], [0, 1], None, [50, 60], [0, 180, 0, 256]
                    )
                    cv2.normalize(hist, hist)

                    if prev_hist is not None:
                        score = cv2.compareHist(
                            prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA
                        )
                        if score > self.threshold:
                            timestamp = round(frame_idx / fps, 2)
                            # Avoid duplicate boundaries too close together
                            if timestamp - scene_boundaries[-1] > 0.5:
                                scene_boundaries.append(timestamp)
                                logger.debug(
                                    "Scene boundary at %.2fs (score=%.3f)",
                                    timestamp, score,
                                )

                    prev_hist = hist.copy()

                frame_idx += 1
        finally:
            cap.release()

        total_duration = round(frame_idx / fps, 2)
        scene_boundaries.append(total_duration)

        # Convert to (start, end) pairs
        scenes = []
        for i in range(len(scene_boundaries) - 1):
            start = scene_boundaries[i]
            end = scene_boundaries[i + 1]
            if end - start > 0.1:  # Skip very short scenes
                scenes.append((start, end))

        logger.info(
            "Detected %d scenes in %.1fs video (threshold=%.2f)",
            len(scenes), total_duration, self.threshold,
        )
        return scenes

    def verify_with_vision(
        self,
        scenes: list[tuple[float, float]],
        frame_data: list[dict],
        vision_service,
    ) -> list[SceneInfo]:
        """Use a vision model to describe each scene.

        Args:
            scenes: List of (start, end) time tuples from histogram detection.
            frame_data: List of extracted frame dicts with 'timestamp' and 'pil_image'.
            vision_service: A VisionService instance (OpenVLM/Moondream).

        Returns:
            List of SceneInfo with AI-generated descriptions.
        """
        verified_scenes = []

        for idx, (start, end) in enumerate(scenes):
            mid_time = (start + end) / 2.0

            # Find the frame closest to the midpoint of this scene
            closest_frame = min(
                frame_data,
                key=lambda f: abs(f["timestamp"] - mid_time),
            )

            try:
                description = vision_service.caption(closest_frame["pil_image"])
            except Exception as e:
                logger.warning("Vision failed for scene %d: %s", idx, e)
                description = f"Scene from {start:.1f}s to {end:.1f}s"

            verified_scenes.append(
                SceneInfo(
                    scene_index=idx,
                    start_time=start,
                    end_time=end,
                    duration=round(end - start, 2),
                    description=description,
                    thumbnail_path=closest_frame.get("path"),
                    confidence=0.85,
                )
            )

        logger.info("Verified %d scenes with vision model", len(verified_scenes))
        return verified_scenes
