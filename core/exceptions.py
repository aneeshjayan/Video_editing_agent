class VideoEditorError(Exception):
    """Base exception for video editing agent."""


class FFmpegError(VideoEditorError):
    """FFmpeg command execution failed."""


class FrameExtractionError(VideoEditorError):
    """Failed to extract frames from video."""


class SceneDetectionError(VideoEditorError):
    """Failed to detect scenes in video."""


class VisionServiceError(VideoEditorError):
    """Vision model API call failed."""



class EditPlanValidationError(VideoEditorError):
    """Edit plan contains invalid operations or timestamps."""


class VideoFormatError(VideoEditorError):
    """Unsupported or invalid video format."""
