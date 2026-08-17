from datetime import UTC, datetime

import pytest
from tests.conftest import (
    FIXED_NOW,
    FakeSkillItemRepository,
    FixedClock,
    StubScheduler,
)

from vocab_api.application.use_cases.quiz import GetModuleQuiz, GradeQuiz
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import (
    CurriculumMap,
    LadderEntry,
    LevelOverview,
    ModuleAvailability,
)
from vocab_api.domain.curriculum.progress import ModuleProgress, ModuleStatus
from vocab_api.domain.curriculum.quiz import Quiz, QuizItem, QuizItemType
from vocab_api.domain.curriculum.skill_item import LEECH_LAPSES, SkillItem
from vocab_api.domain.curriculum.track import Track
from vocab_api.domain.shared.errors import CurriculumQuizNotFound


class FakeContent:
    def __init__(self) -> None:
        self._has_quiz = {"b1.grammar.articles"}
        self._available = {"b1.grammar.articles"}
        self._quizzes = {
            "b1.grammar.articles": Quiz(
                module_id="b1.grammar.articles",
                items=(
                    QuizItem(
                        id="q1",
                        module_id="b1.grammar.articles",
                        type=QuizItemType.MCQ,
                        skill="art.indefinite",
                        prompt="Pick the article",
                        explanation="Use 'an' before a vowel sound.",
                        options=("a", "an"),
                        answer_index=1,
                    ),
                    QuizItem(
                        id="q2",
                        module_id="b1.grammar.articles",
                        type=QuizItemType.CLOZE,
                        skill="art.definite",
                        prompt="She plays the violin.",
                        explanation="Musical instruments take 'the'.",
                        answers=("the",),
                    ),
                ),
            )
        }

    def has_quiz(self, module_id: str) -> bool:
        return module_id in self._has_quiz

    def is_available(self, module_id: str) -> bool:
        return module_id in self._available

    def quiz(self, module_id: str) -> Quiz:
        return self._quizzes[module_id]

    def map(self) -> CurriculumMap[LadderEntry]:
        return CurriculumMap(
            levels=(
                LevelOverview(
                    level=Level.B1,
                    entries=(
                        LadderEntry(
                            id="b1.grammar.articles",
                            title="",
                            track=Track.GRAMMAR,
                            availability=ModuleAvailability.AVAILABLE,
                        ),
                    ),
                ),
            )
        )


class FakeProgress:
    def __init__(self) -> None:
        self._items: dict[str, ModuleProgress] = {}

    def seed(self, progress: ModuleProgress) -> None:
        self._items[progress.module_id] = progress

    async def get(self, module_id: str) -> ModuleProgress:
        return self._items.get(module_id, ModuleProgress(module_id=module_id))

    async def mark_quiz_attempted(
        self, module_id: str, best_score: float, now: datetime
    ) -> ModuleProgress:
        existing = self._items.get(module_id, ModuleProgress(module_id=module_id))
        derived = existing.derive_status(
            lesson_read_at=existing.lesson_read_at, quiz_attempted=True, now=now
        )
        updated = ModuleProgress(
            module_id=module_id,
            status=derived.status,
            lesson_read_at=derived.lesson_read_at,
            quiz_best_score=max(existing.quiz_best_score or 0.0, best_score),
            completed_at=derived.completed_at,
        )
        self._items[module_id] = updated
        return updated

    async def list(self) -> list[ModuleProgress]:
        return list(self._items.values())


class FakeAttempts:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str, bool]] = []

    async def record(
        self,
        module_id: str,
        item_id: str,
        given: str,
        correct: bool,
        answered_at: datetime,
    ) -> None:
        self.rows.append((module_id, item_id, given, correct))


async def test_get_module_quiz_returns_quiz_and_progress():
    content = FakeContent()
    progress = FakeProgress()
    progress.seed(
        ModuleProgress(module_id="b1.grammar.articles", quiz_best_score=50.0)
    )

    quiz, module_progress = await GetModuleQuiz(content, progress).execute("b1.grammar.articles")

    assert quiz.module_id == "b1.grammar.articles"
    assert len(quiz.items) == 2
    assert module_progress.quiz_best_score == 50.0


async def test_get_module_quiz_missing_raises():
    with pytest.raises(CurriculumQuizNotFound):
        await GetModuleQuiz(FakeContent(), FakeProgress()).execute("x1.missing.slug")


async def test_grade_quiz_grades_all_answers_and_records_attempts():
    content = FakeContent()
    progress = FakeProgress()
    attempts = FakeAttempts()
    clock = FixedClock(datetime(2026, 8, 17, 9, 0, tzinfo=UTC))

    outcome = await GradeQuiz(
        content, progress, attempts, clock, FakeSkillItemRepository(), StubScheduler()
    ).execute(
        "b1.grammar.articles",
        [("q1", "1"), ("q2", "the")],
    )

    assert outcome.score == 100.0
    assert outcome.status is ModuleStatus.NOT_STARTED
    assert outcome.next_module_id == "b1.grammar.articles"
    assert [item.correct for item in outcome.items] == [True, True]
    assert outcome.items[0].explanation == "Use 'an' before a vowel sound."
    assert attempts.rows == [
        ("b1.grammar.articles", "q1", "1", True),
        ("b1.grammar.articles", "q2", "the", True),
    ]


async def test_grade_quiz_upserts_skill_item_on_failure():
    content = FakeContent()
    skills = FakeSkillItemRepository()

    outcome = await GradeQuiz(
        content, FakeProgress(), FakeAttempts(), FixedClock(), skills, StubScheduler()
    ).execute(
        "b1.grammar.articles",
        [("q1", "0"), ("q2", "wrong")],
    )

    assert outcome.items[0].correct is False
    assert outcome.items[1].correct is False
    art_indefinite = await skills.by_skill("art.indefinite")
    art_definite = await skills.by_skill("art.definite")
    assert art_indefinite is not None
    assert art_indefinite.module_id == "b1.grammar.articles"
    assert art_indefinite.source_item_id == "q1"
    assert art_indefinite.fsrs.due == FIXED_NOW
    assert art_definite is not None
    assert art_definite.source_item_id == "q2"


async def test_grade_quiz_one_skill_item_per_skill_and_correct_answers_advance_it():
    content = FakeContent()
    clock = FixedClock(datetime(2026, 8, 17, 9, 0, tzinfo=UTC))
    skills = FakeSkillItemRepository()
    use_case = GradeQuiz(
        content, FakeProgress(), FakeAttempts(), clock, skills, StubScheduler()
    )
    await use_case.execute("b1.grammar.articles", [("q1", "0")])
    created = await skills.by_skill("art.indefinite")
    assert created is not None and created.id is not None
    before = created.fsrs.due

    await use_case.execute("b1.grammar.articles", [("q1", "1")])

    # The skill item is not duplicated; a correct answer advances its schedule.
    assert await skills.by_skill("art.indefinite") is not None
    assert (await skills.by_skill("art.indefinite")).id == created.id
    assert (await skills.by_skill("art.indefinite")).fsrs.due > before


async def test_grade_quiz_correct_answer_preserves_lapse_count():
    # A correct answer records a Good review but must not erase the skill's
    # accumulated lapses (its leech/weak-spot history) — mirrors the invariant
    # that RecordSkillReview upholds via the real, lapse-agnostic scheduler.
    content = FakeContent()
    skills = FakeSkillItemRepository()
    leech = await skills.add(
        SkillItem(
            skill="art.indefinite",
            module_id="b1.grammar.articles",
            source_item_id="q1",
            fsrs=FsrsState(due=FIXED_NOW, state=2, stability=1.0, lapses=LEECH_LAPSES),
        )
    )
    use_case = GradeQuiz(
        content, FakeProgress(), FakeAttempts(), FixedClock(), skills, StubScheduler()
    )

    await use_case.execute("b1.grammar.articles", [("q1", "1")])

    updated = await skills.by_skill("art.indefinite")
    assert updated is not None
    assert updated.id == leech.id
    assert updated.fsrs.lapses == LEECH_LAPSES
    assert updated.is_leech is True


async def test_grade_quiz_completes_module_once_lesson_read():
    content = FakeContent()
    progress = FakeProgress()
    progress.seed(
        ModuleProgress(
            module_id="b1.grammar.articles",
            status=ModuleStatus.IN_PROGRESS,
            lesson_read_at=datetime(2026, 8, 17, 8, 0, tzinfo=UTC),
        )
    )
    attempts = FakeAttempts()

    outcome = await GradeQuiz(
        content, progress, attempts, FixedClock(), FakeSkillItemRepository(), StubScheduler()
    ).execute(
        "b1.grammar.articles",
        [("q1", "0"), ("q2", "the")],
    )

    assert outcome.score == 50.0
    assert outcome.status is ModuleStatus.COMPLETED


async def test_grade_quiz_skips_unknown_item_ids():
    content = FakeContent()
    attempts = FakeAttempts()

    outcome = await GradeQuiz(
        content, FakeProgress(), attempts, FixedClock(), FakeSkillItemRepository(), StubScheduler()
    ).execute(
        "b1.grammar.articles",
        [("q1", "1"), ("missing", "x")],
    )

    assert len(outcome.items) == 1
    assert outcome.items[0].item_id == "q1"


async def test_grade_quiz_missing_module_raises():
    with pytest.raises(CurriculumQuizNotFound):
        await GradeQuiz(
            FakeContent(), FakeProgress(), FakeAttempts(), FixedClock(),
            FakeSkillItemRepository(), StubScheduler(),
        ).execute(
            "x1.missing.slug", []
        )
