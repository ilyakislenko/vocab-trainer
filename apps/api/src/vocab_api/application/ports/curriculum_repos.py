from datetime import datetime
from typing import Protocol

from vocab_api.domain.curriculum.progress import LearnerProfile, ModuleProgress


class LearnerProfileRepository(Protocol):
    async def get(self) -> LearnerProfile: ...
    async def save(self, profile: LearnerProfile) -> None: ...


class ModuleProgressRepository(Protocol):
    async def get(self, module_id: str) -> ModuleProgress: ...
    async def save(self, progress: ModuleProgress) -> None: ...
    async def list(self) -> list[ModuleProgress]: ...
    async def mark_lesson_read(self, module_id: str, now: datetime) -> ModuleProgress: ...
    async def mark_quiz_attempted(
        self, module_id: str, best_score: float, now: datetime
    ) -> ModuleProgress: ...


class QuizAttemptRepository(Protocol):
    """Append-only log of individual quiz answers (used by review in Phase 2)."""

    async def record(
        self,
        module_id: str,
        item_id: str,
        given: str,
        correct: bool,
        answered_at: datetime,
    ) -> None: ...