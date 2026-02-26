from __future__ import annotations

from core.exceptions import EditPlanValidationError
from models.schemas import EditPlan


class EditPlanValidator:
    """Validates edit plans before execution."""

    @staticmethod
    def validate(plan: EditPlan) -> list[str]:
        """Validate an edit plan. Returns list of error messages (empty = valid)."""
        errors = []
        duration = plan.original_video.duration_seconds

        if not plan.steps:
            errors.append("Edit plan has no steps")
            return errors

        for i, step in enumerate(plan.steps):
            if step.start_time is not None and step.start_time < 0:
                errors.append(f"Step {i}: start_time cannot be negative ({step.start_time})")

            if step.end_time is not None and step.end_time < 0:
                errors.append(f"Step {i}: end_time cannot be negative ({step.end_time})")

            if step.start_time is not None and step.start_time > duration:
                errors.append(
                    f"Step {i}: start_time {step.start_time:.1f}s exceeds "
                    f"video duration {duration:.1f}s"
                )

            if step.end_time is not None and step.end_time > duration:
                errors.append(
                    f"Step {i}: end_time {step.end_time:.1f}s exceeds "
                    f"video duration {duration:.1f}s"
                )

            if (
                step.start_time is not None
                and step.end_time is not None
                and step.start_time >= step.end_time
            ):
                errors.append(
                    f"Step {i}: start_time ({step.start_time:.1f}s) must be "
                    f"before end_time ({step.end_time:.1f}s)"
                )

            if step.transition_duration is not None and step.transition_duration <= 0:
                errors.append(
                    f"Step {i}: transition_duration must be positive "
                    f"({step.transition_duration})"
                )

            if step.speed_factor is not None and step.speed_factor <= 0:
                errors.append(
                    f"Step {i}: speed_factor must be positive ({step.speed_factor})"
                )

        return errors

    @staticmethod
    def validate_or_raise(plan: EditPlan) -> None:
        """Validate and raise if invalid."""
        errors = EditPlanValidator.validate(plan)
        if errors:
            raise EditPlanValidationError(
                f"Edit plan validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
