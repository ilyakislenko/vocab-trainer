from datetime import UTC, datetime
from typing import overload

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.progress import LearnerProfile, ModuleProgress, ModuleStatus
from vocab_api.domain.curriculum.skill_item import SkillItem
from vocab_api.infrastructure.persistence.curriculum_tables import (
    LearnerProfileRow,
    ModuleProgressRow,
    SkillItemRow,
)


@overload
def _as_utc(dt: datetime) -> datetime: ...
@overload
def _as_utc(dt: None) -> None: ...
def _as_utc(dt: datetime | None) -> datetime | None:
    # Same SQLite naive-datetime round-trip handling as card mappers: re-attach
    # UTC so the domain invariant (tz-aware datetimes) holds after a DB read.
    return dt.replace(tzinfo=UTC) if dt is not None and dt.tzinfo is None else dt


def _as_level(value: str | None) -> Level | None:
    return Level(value) if value is not None else None


def learner_profile_from_row(row: LearnerProfileRow) -> LearnerProfile:
    return LearnerProfile(
        placement_level=_as_level(row.placement_level),
        current_module_id=row.current_module_id,
    )


def learner_profile_to_row(profile: LearnerProfile) -> LearnerProfileRow:
    return LearnerProfileRow(
        id=1,
        placement_level=(
            profile.placement_level.value if profile.placement_level is not None else None
        ),
        current_module_id=profile.current_module_id,
    )


def module_progress_from_row(row: ModuleProgressRow) -> ModuleProgress:
    return ModuleProgress(
        module_id=row.module_id,
        status=ModuleStatus(row.status),
        lesson_read_at=_as_utc(row.lesson_read_at),
        quiz_best_score=row.quiz_best_score,
        completed_at=_as_utc(row.completed_at),
    )


def module_progress_to_row(progress: ModuleProgress) -> ModuleProgressRow:
    return ModuleProgressRow(
        module_id=progress.module_id,
        status=progress.status.value,
        lesson_read_at=progress.lesson_read_at,
        quiz_best_score=progress.quiz_best_score,
        completed_at=progress.completed_at,
    )


def skill_item_from_row(row: SkillItemRow) -> SkillItem:
    return SkillItem(
        id=row.id,
        skill=row.skill,
        module_id=row.module_id,
        source_item_id=row.source_item_id,
        fsrs=FsrsState(
            due=_as_utc(row.fsrs_due),
            state=row.fsrs_state,
            step=row.fsrs_step,
            stability=row.fsrs_stability,
            difficulty=row.fsrs_difficulty,
            last_review=_as_utc(row.fsrs_last_review),
            lapses=row.fsrs_lapses,
        ),
    )


def skill_item_to_row(item: SkillItem) -> SkillItemRow:
    return SkillItemRow(
        id=item.id,
        skill=item.skill,
        module_id=item.module_id,
        source_item_id=item.source_item_id,
        fsrs_state=item.fsrs.state,
        fsrs_step=item.fsrs.step,
        fsrs_stability=item.fsrs.stability,
        fsrs_difficulty=item.fsrs.difficulty,
        fsrs_due=item.fsrs.due,
        fsrs_last_review=item.fsrs.last_review,
        fsrs_lapses=item.fsrs.lapses,
    )