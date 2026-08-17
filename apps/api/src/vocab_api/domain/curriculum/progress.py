from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from vocab_api.domain.curriculum.level import Level


class ModuleStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ModuleProgress:
    """Per-module learner state.

    `quiz_best_score` is informational only — navigation is free, so a module
    completes the moment its lesson is read and its quiz is attempted at least
    once, whatever the score.
    """

    module_id: str
    status: ModuleStatus = ModuleStatus.NOT_STARTED
    lesson_read_at: datetime | None = None
    quiz_best_score: float | None = None
    completed_at: datetime | None = None

    def derive_status(
        self, lesson_read_at: datetime | None, quiz_attempted: bool, now: datetime
    ) -> "ModuleProgress":
        completed = lesson_read_at is not None and quiz_attempted
        if completed:
            status = ModuleStatus.COMPLETED
            completed_at: datetime | None = self.completed_at or now
        elif lesson_read_at is not None:
            status = ModuleStatus.IN_PROGRESS
            completed_at = self.completed_at
        else:
            status = ModuleStatus.NOT_STARTED
            completed_at = self.completed_at
        return ModuleProgress(
            module_id=self.module_id,
            status=status,
            lesson_read_at=lesson_read_at or self.lesson_read_at,
            quiz_best_score=self.quiz_best_score,
            completed_at=completed_at,
        )


@dataclass(frozen=True, slots=True)
class LearnerProfile:
    """The single learner's mutable state.

    A singleton row (id=1) — there is no auth and no user concept in the app.
    `current_module_id` is the recommended next module; it is a suggestion, not
    a gate (free navigation).
    """

    placement_level: Level | None = None
    current_module_id: str | None = None