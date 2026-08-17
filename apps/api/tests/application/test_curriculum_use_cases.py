from datetime import UTC, datetime

import pytest
from tests.conftest import FakeLearnerProfileRepository, FixedClock

from vocab_api.application.use_cases.curriculum import (
    GetCurriculumMap,
    GetLesson,
    GetModule,
    GetRecommendedModule,
    MarkLessonRead,
)
from vocab_api.domain.curriculum.lesson import Lesson
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import (
    CurriculumMap,
    LadderEntry,
    LevelOverview,
    ModuleAvailability,
)
from vocab_api.domain.curriculum.module import Module, Reference
from vocab_api.domain.curriculum.progress import ModuleProgress, ModuleStatus
from vocab_api.domain.curriculum.track import Track
from vocab_api.domain.shared.errors import (
    CurriculumLessonNotFound,
    CurriculumModuleNotFound,
)

READ_AT = datetime(2026, 8, 16, 9, 0, tzinfo=UTC)


class FakeCurriculumContent:
    def __init__(self) -> None:
        self._available = {"b1.grammar.articles", "b1.grammar.conditionals-wish"}
        self._modules = {
            "b1.grammar.articles": Module(
                id="b1.grammar.articles",
                title="Articles",
                objectives=("Pick the article",),
                skills=("art.definite",),
                references=(Reference(book="Grammar", locator="U1"),),
                estimated_minutes=5,
                order=0,
            ),
            "b1.grammar.conditionals-wish": Module(
                id="b1.grammar.conditionals-wish",
                title="Conditionals",
                objectives=("Build the second conditional",),
                skills=("cond.second",),
                references=(),
                estimated_minutes=6,
                order=1,
            ),
        }
        self._lessons = {
            "b1.grammar.articles": Lesson(
                id="b1.grammar.articles",
                title="Articles",
                markdown="# Articles\n\nBody.",
                estimated_minutes=5,
                objectives=("Pick the article",),
                skills=("art.definite",),
            ),
            "b1.grammar.conditionals-wish": Lesson(
                id="b1.grammar.conditionals-wish",
                title="Conditionals",
                markdown="# Conditionals\n\nBody.",
                estimated_minutes=6,
                objectives=("Build the second conditional",),
                skills=("cond.second",),
            ),
        }
        self._levels = (
            LevelOverview(
                level=Level.B1,
                entries=(
                    LadderEntry(
                        id="b1.grammar.articles",
                        title="",
                        track=Track.GRAMMAR,
                        availability=ModuleAvailability.AVAILABLE,
                    ),
                    LadderEntry(
                        id="b1.grammar.conditionals-wish",
                        title="",
                        track=Track.GRAMMAR,
                        availability=ModuleAvailability.AVAILABLE,
                    ),
                    LadderEntry(
                        id="a1.grammar.to-be",
                        title="To be",
                        track=Track.GRAMMAR,
                        availability=ModuleAvailability.AUTHORING,
                    ),
                ),
            ),
        )

    def map(self) -> CurriculumMap:
        return CurriculumMap(levels=self._levels)

    def module(self, module_id: str) -> Module:
        if module_id not in self._modules:
            raise CurriculumModuleNotFound(module_id)
        return self._modules[module_id]

    def lesson(self, module_id: str) -> Lesson:
        if module_id not in self._lessons:
            raise CurriculumModuleNotFound(module_id)
        return self._lessons[module_id]

    def has_lesson(self, module_id: str) -> bool:
        return module_id in self._lessons

    def has_quiz(self, module_id: str) -> bool:
        return False

    def is_available(self, module_id: str) -> bool:
        return module_id in self._available


class FakeModuleProgressRepository:
    def __init__(self) -> None:
        self._items: dict[str, ModuleProgress] = {}

    async def get(self, module_id: str) -> ModuleProgress:
        return self._items.get(module_id, ModuleProgress(module_id=module_id))

    async def save(self, progress: ModuleProgress) -> None:
        self._items[progress.module_id] = progress

    async def list(self) -> list[ModuleProgress]:
        return list(self._items.values())

    async def mark_lesson_read(self, module_id: str, now: datetime) -> ModuleProgress:
        current = self._items.get(module_id, ModuleProgress(module_id=module_id))
        updated = current.derive_status(lesson_read_at=now, quiz_attempted=False, now=now)
        self._items[module_id] = updated
        return updated


async def test_get_curriculum_map_lists_all_levels_with_progress():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()
    await repo.mark_lesson_read("b1.grammar.articles", READ_AT)

    board = await GetCurriculumMap(content, repo).execute()

    assert [section.level for section in board.levels] == [Level.B1]
    rows = {row.id: row for row in board.levels[0].entries}
    assert rows["b1.grammar.articles"].status is ModuleStatus.IN_PROGRESS
    assert rows["b1.grammar.conditionals-wish"].status is ModuleStatus.NOT_STARTED
    assert rows["a1.grammar.to-be"].availability is ModuleAvailability.AUTHORING


async def test_get_module_returns_module_and_progress():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()

    module, progress = await GetModule(content, repo).execute("b1.grammar.articles")

    assert module.id == "b1.grammar.articles"
    assert progress.status is ModuleStatus.NOT_STARTED


async def test_get_module_missing_raises():
    with pytest.raises(CurriculumModuleNotFound):
        await GetModule(
            FakeCurriculumContent(), FakeModuleProgressRepository()
        ).execute("x1.missing.slug")


async def test_get_lesson_returns_lesson_for_available_module():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()

    lesson, progress = await GetLesson(content, repo).execute("b1.grammar.articles")

    assert lesson.title == "Articles"
    assert "# Articles" in lesson.markdown
    assert progress.status is ModuleStatus.NOT_STARTED


async def test_get_lesson_for_authoring_module_raises():
    content = FakeCurriculumContent()
    with pytest.raises(CurriculumLessonNotFound):
        await GetLesson(content, FakeModuleProgressRepository()).execute("a1.grammar.to-be")


async def test_mark_lesson_read_is_idempotent():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()

    first = await MarkLessonRead(content, repo, FixedClock(READ_AT)).execute("b1.grammar.articles")
    second = await MarkLessonRead(content, repo, FixedClock(READ_AT)).execute("b1.grammar.articles")

    assert first.status is ModuleStatus.IN_PROGRESS
    assert second.status is ModuleStatus.IN_PROGRESS
    assert second.lesson_read_at == READ_AT


async def test_mark_lesson_read_missing_raises():
    content = FakeCurriculumContent()
    with pytest.raises(CurriculumLessonNotFound):
        await MarkLessonRead(
            content, FakeModuleProgressRepository(), FixedClock()
        ).execute("x1.missing.slug")


async def test_get_recommended_module_skips_completed_and_authoring():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()
    await repo.save(
        ModuleProgress(module_id="b1.grammar.articles", status=ModuleStatus.COMPLETED)
    )

    recommended = await GetRecommendedModule(
        content, repo, FakeLearnerProfileRepository()
    ).execute()

    assert recommended == "b1.grammar.conditionals-wish"


async def test_get_recommended_module_returns_in_progress_first():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()
    await repo.mark_lesson_read("b1.grammar.articles", READ_AT)

    recommended = await GetRecommendedModule(
        content, repo, FakeLearnerProfileRepository()
    ).execute()

    assert recommended == "b1.grammar.articles"


async def test_get_recommended_module_none_when_all_available_are_complete():
    content = FakeCurriculumContent()
    repo = FakeModuleProgressRepository()
    await repo.save(ModuleProgress(module_id="b1.grammar.articles", status=ModuleStatus.COMPLETED))
    await repo.save(
        ModuleProgress(module_id="b1.grammar.conditionals-wish", status=ModuleStatus.COMPLETED)
    )

    recommended = await GetRecommendedModule(
        content, repo, FakeLearnerProfileRepository()
    ).execute()

    assert recommended is None