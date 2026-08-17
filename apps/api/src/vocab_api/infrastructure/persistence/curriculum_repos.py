from datetime import datetime

from sqlmodel import select

from vocab_api.application.ports.curriculum_repos import (
    LearnerProfileRepository,
    ModuleProgressRepository,
    QuizAttemptRepository,
    SkillItemRepository,
)
from vocab_api.domain.curriculum.progress import (
    LearnerProfile,
    ModuleProgress,
    ModuleStatus,
)
from vocab_api.domain.curriculum.skill_item import LEECH_LAPSES, SkillItem
from vocab_api.domain.shared.errors import SkillItemNotFound
from vocab_api.infrastructure.persistence.curriculum_mappers import (
    learner_profile_from_row,
    learner_profile_to_row,
    module_progress_from_row,
    module_progress_to_row,
    skill_item_from_row,
    skill_item_to_row,
)
from vocab_api.infrastructure.persistence.curriculum_tables import (
    LearnerProfileRow,
    ModuleProgressRow,
    QuizAttemptRow,
    SkillItemRow,
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

    async def mark_quiz_attempted(
        self, module_id: str, best_score: float, now: datetime
    ) -> ModuleProgress:
        # A module completes the moment its lesson is read AND its quiz is
        # attempted at least once (any score, no threshold). Best score is
        # kept monotonically. Idempotent for repeated attempts.
        async with self._db.session() as session:
            row = await session.get(ModuleProgressRow, module_id)
            existing = (
                module_progress_from_row(row)
                if row is not None
                else ModuleProgress(module_id=module_id)
            )
            score = max(existing.quiz_best_score or 0.0, best_score)
            updated = ModuleProgress(
                module_id=module_id,
                status=existing.status,
                lesson_read_at=existing.lesson_read_at,
                quiz_best_score=score,
                completed_at=existing.completed_at,
            ).derive_status(lesson_read_at=existing.lesson_read_at, quiz_attempted=True, now=now)
            await session.merge(module_progress_to_row(updated))
            await session.commit()
        return updated


class SqlQuizAttemptRepository(QuizAttemptRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def record(
        self,
        module_id: str,
        item_id: str,
        given: str,
        correct: bool,
        answered_at: datetime,
    ) -> None:
        row = QuizAttemptRow(
            module_id=module_id,
            item_id=item_id,
            given=given,
            correct=correct,
            answered_at=answered_at,
        )
        async with self._db.session() as session:
            session.add(row)
            await session.commit()


class SqlSkillItemRepository(SkillItemRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def by_skill(self, skill: str) -> SkillItem | None:
        statement = select(SkillItemRow).where(SkillItemRow.skill == skill).limit(1)
        async with self._db.session() as session:
            row = (await session.execute(statement)).scalar_one_or_none()
        return skill_item_from_row(row) if row is not None else None

    async def get(self, skill_item_id: int) -> SkillItem:
        async with self._db.session() as session:
            row = await session.get(SkillItemRow, skill_item_id)
        if row is None:
            raise SkillItemNotFound(skill_item_id)
        return skill_item_from_row(row)

    async def add(self, item: SkillItem) -> SkillItem:
        row = skill_item_to_row(item)
        async with self._db.session() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return skill_item_from_row(row)

    async def save(self, item: SkillItem) -> None:
        row = skill_item_to_row(item)
        async with self._db.session() as session:
            await session.merge(row)
            await session.commit()

    async def due(self, now: datetime, limit: int) -> list[SkillItem]:
        # SkillItemRow.fsrs_due is a plain datetime class attribute; mypy can't
        # see the runtime InstrumentedAttribute order_by() expects (same quirk
        # as CardRow).
        statement = (
            select(SkillItemRow)
            .where(SkillItemRow.fsrs_due <= now)
            .order_by(SkillItemRow.fsrs_due)  # type: ignore[arg-type]
            .limit(limit)
        )
        async with self._db.session() as session:
            rows = (await session.execute(statement)).scalars().all()
        return [skill_item_from_row(row) for row in rows]

    async def leeches(self, limit: int) -> list[SkillItem]:
        # Leech detection orders the weakest skills first: highest lapse count,
        # then the soonest due.
        statement = (
            select(SkillItemRow)
            .where(SkillItemRow.fsrs_lapses >= LEECH_LAPSES)
            .order_by(
                SkillItemRow.fsrs_lapses.desc(),  # type: ignore[attr-defined]  # sqlmodel class attr is typed int
                SkillItemRow.fsrs_due,  # type: ignore[arg-type]  # same InstrumentedAttribute quirk
            )
            .limit(limit)
        )
        async with self._db.session() as session:
            rows = (await session.execute(statement)).scalars().all()
        return [skill_item_from_row(row) for row in rows]