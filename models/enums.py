from enum import Enum


class TransitionType(str, Enum):
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE_LEFT = "wipeleft"
    WIPE_RIGHT = "wiperight"
    SLIDE_LEFT = "slideleft"
    SLIDE_RIGHT = "slideright"
    NONE = "none"


class EditOperation(str, Enum):
    TRIM = "trim"
    CONCAT = "concat"
    TRANSITION = "transition"
    SPEED = "speed"
    REMOVE_SEGMENT = "remove_segment"


class PipelineStage(str, Enum):
    UPLOAD = "upload"
    FRAME_EXTRACTION = "frame_extraction"
    SCENE_DETECTION = "scene_detection"
    CONTENT_ANALYSIS = "content_analysis"
    EDIT_PLANNING = "edit_planning"
    COMMAND_GENERATION = "command_generation"
    EXECUTION = "execution"
    DELIVERY = "delivery"


class PipelineStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
