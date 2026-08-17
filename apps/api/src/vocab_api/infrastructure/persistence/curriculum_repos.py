from datetime import datetime

from sqlmodel import select

from vocab_api.application.ports.curriculum_repos import (
    LearnerProfileRepository,
    ModuleProgressRepository,
)
from vocab_api.domain.curriculum.progress import (
    LearnerProfile,
    ModuleProgress,
    ModuleStatus,
)
from vocab_api.infrastructure.persistence.curriculum_mappers import (
    learner_profile_from_row,
    learner_profile_to_row,
    module_progress_from_row,
    module_progress_to_row,
)
from vocab_api.infrastructure.persistence.curriculum_tables import (
    LearnerProfileRow,
    ModuleProgressRow,
)
from vocab_api.infrastructure.persistence.engine import Database


class SqlLearnerProfileRepository(LearnerProfileRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self) -> LearnerProfile:
        async with self._db.session() as session:
            row = await session.get(LearnerProfileRow, 1)
            if row is None:
                return LearnerProfile()
            return learner_profile_from_row(row)

    async def save(self, profile: LearnerProfile) -> None:
        row = learner_profile_to_row(profile)
        async with self._db.session() as session:
            await session.merge(row)
            await session.commit()


class SqlModuleProgressRepository(ModuleProgressRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self, module_id: str) -> ModuleProgress:
        async with self._db.session() as session:
            row = await session.get(ModuleProgressRow, module_id)
            if row is None:
                return ModuleProgress(module_id=module_id)
            return module_progress_from_row(row)

    async def save(self, progress: ModuleProgress) -> None:
        row = module_progress_to_row(progress)
        async with self._db.session() as session:
            await session.merge(row)
            await session.commit()

    async def list(self) -> list[ModuleProgress]:
        statement = select(ModuleProgressRow)
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [module_progress_from_row(row) for row in rows]

    async def mark_lesson_read(self, module_id: str, now: datetime) -> ModuleProgress:
        # Lesson read flips a module from not_started to in_progress; it is not
        # completed until the quiz is attempted (Phase 1), so status is derived
        # here from the existing row. Idempotent: an existing read timestamp is
        # preserved, so repeated marks never move the recorded time.
        async with self._db.session() as session:
            row = await session.get(ModuleProgressRow, module_id)
            existing = (
                module_progress_from_row(row)
                if row is not None
                else ModuleProgress(module_id=module_id)
            )
            read_at = existing.lesson_read_at if existing.lesson_read_at is not None else now
            updated = ModuleProgress(
                module_id=module_id,
                status=ModuleStatus.IN_PROGRESS,
                lesson_read_at=read_at,
                quiz_best_score=existing.quiz_best_score,
                completed_at=existing.completed_at,
            )
            await session.merge(module_progress_to_row(updated))
            await session.commit()
        return updated