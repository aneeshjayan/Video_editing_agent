import pytest

from core.edit_plan import EditPlanValidator
from core.exceptions import EditPlanValidationError
from models.enums import EditOperation, TransitionType
from models.schemas import EditPlan, EditStep, VideoMetadata


def make_video_metadata(duration: float = 60.0) -> VideoMetadata:
    return VideoMetadata(
        file_path="test.mp4",
        duration_seconds=duration,
        width=1920,
        height=1080,
        fps=30.0,
        codec="h264",
        file_size_bytes=10_000_000,
    )


class TestEditPlanValidator:
    def test_valid_trim_plan(self):
        """Valid trim plan should pass validation."""
        plan = EditPlan(
            original_video=make_video_metadata(60.0),
            steps=[
                EditStep(
                    operation=EditOperation.TRIM,
                    start_time=10.0,
                    end_time=50.0,
                    description="Trim to 10-50s",
                )
            ],
        )
        errors = EditPlanValidator.validate(plan)
        assert errors == []

    def test_empty_steps_fails(self):
        """Plan with no steps should fail."""
        plan = EditPlan(
            original_video=make_video_metadata(),
            steps=[],
        )
        errors = EditPlanValidator.validate(plan)
        assert len(errors) == 1
        assert "no steps" in errors[0]

    def test_start_after_end_fails(self):
        """start_time >= end_time should fail."""
        plan = EditPlan(
            original_video=make_video_metadata(),
            steps=[
                EditStep(
                    operation=EditOperation.TRIM,
                    start_time=30.0,
                    end_time=20.0,
                    description="Invalid",
                )
            ],
        )
        errors = EditPlanValidator.validate(plan)
        assert any("before end_time" in e for e in errors)

    def test_timestamp_exceeds_duration(self):
        """Timestamps beyond video duration should fail."""
        plan = EditPlan(
            original_video=make_video_metadata(30.0),
            steps=[
                EditStep(
                    operation=EditOperation.TRIM,
                    start_time=0.0,
                    end_time=45.0,
                    description="Too long",
                )
            ],
        )
        errors = EditPlanValidator.validate(plan)
        assert any("exceeds" in e for e in errors)

    def test_negative_timestamp_fails(self):
        """Negative timestamps should fail."""
        plan = EditPlan(
            original_video=make_video_metadata(),
            steps=[
                EditStep(
                    operation=EditOperation.TRIM,
                    start_time=-5.0,
                    end_time=10.0,
                    description="Negative start",
                )
            ],
        )
        errors = EditPlanValidator.validate(plan)
        assert any("negative" in e for e in errors)

    def test_negative_speed_factor_fails(self):
        """Negative speed factor should fail."""
        plan = EditPlan(
            original_video=make_video_metadata(),
            steps=[
                EditStep(
                    operation=EditOperation.SPEED,
                    speed_factor=-1.0,
                    description="Invalid speed",
                )
            ],
        )
        errors = EditPlanValidator.validate(plan)
        assert any("speed_factor" in e for e in errors)

    def test_validate_or_raise(self):
        """validate_or_raise should raise on invalid plans."""
        plan = EditPlan(
            original_video=make_video_metadata(),
            steps=[],
        )
        with pytest.raises(EditPlanValidationError):
            EditPlanValidator.validate_or_raise(plan)

    def test_multiple_valid_steps(self):
        """Plan with multiple valid steps should pass."""
        plan = EditPlan(
            original_video=make_video_metadata(60.0),
            steps=[
                EditStep(
                    operation=EditOperation.TRIM,
                    start_time=0.0,
                    end_time=20.0,
                    description="Keep first 20s",
                ),
                EditStep(
                    operation=EditOperation.TRIM,
                    start_time=40.0,
                    end_time=60.0,
                    description="Keep last 20s",
                ),
                EditStep(
                    operation=EditOperation.CONCAT,
                    description="Join the two clips",
                ),
            ],
        )
        errors = EditPlanValidator.validate(plan)
        assert errors == []
