from datetime import UTC, datetime, timedelta

from tests.conftest import (
    FakeCardRepository,
    FakeDeckRepository,
    FakeLearnerProfileRepository,
    FakeReviewLogRepository,
    FakeSkillItemRepository,
    FixedClock,
)

from vocab_api.application.use_cases.curriculum import GetRecommendedModule
from vocab_api.application.use_cases.today import BuildTodaySession
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.curriculum.lesson import Lesson
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import (
    CurriculumMap,
    LadderEntry,
    LevelOverview,
    ModuleAvailability,
)
from vocab_api.domain.curriculum.module import Module, Reference
from vocab_api.domain.curriculum.placement import Placement
from vocab_api.domain.curriculum.progress import ModuleProgress, ModuleStatus
from vocab_api.domain.curriculum.quiz import Quiz, QuizItem, QuizItemType
from vocab_api.domain.curriculum.skill_item import LEECH_LAPSES, SkillItem
from vocab_api.domain.curriculum.today import (
    FocusStep,
    ProduceStep,
    ReadLessonStep,
    ReviewStep,
    TakeQuizStep,
)
from vocab_api.domain.curriculum.track import Track
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.review.review_log import ReviewLogEntry

NOW = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
DUE_AT = datetime(2026, 8, 17, 8, 0, tzinfo=UTC)


class FakeContent:
    def __init__(self) -> None:
        self._available = {"b1.grammar.articles", "b1.grammar.conditionals-wish"}
        self._modules = {
            "b1.grammar.articles": Module(
                id="b1.grammar.articles",
                title="Articles",
                objectives=("Pick the article",),
                skills=("art.definite",),
                references=(Reference(book="Grammar", locator="U1"),),
            ),
            "b1.grammar.conditionals-wish": Module(
                id="b1.grammar.conditionals-wish",
                title="Conditionals",
                objectives=("Build the second conditional",),
                skills=("cond.second",),
                references=(),
            ),
        }
        self._lessons = {
            "b1.grammar.articles": Lesson(
                id="b1.grammar.articles",
                title="Articles",
                markdown="# Articles",
                estimated_minutes=5,
                objectives=("Pick the article",),
                skills=("art.definite",),
            ),
            "b1.grammar.conditionals-wish": Lesson(
                id="b1.grammar.conditionals-wish",
                title="Conditionals",
                markdown="# Conditionals",
                estimated_minutes=6,
                objectives=("Build the second conditional",),
                skills=("cond.second",),
            ),
        }
        self._quizzes = {
            "b1.grammar.articles": Quiz(
                module_id="b1.grammar.articles",
                items=(
                    QuizItem(
                        id="q1",
                        module_id="b1.grammar.articles",
                        type=QuizItemType.MCQ,
                        skill="art.definite",
                        prompt="Pick",
                        explanation="Because.",
                        options=("a", "the"),
                        answer_index=0,
                    ),
                ),
            ),
        }

    def map(self) -> CurriculumMap:
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
                        LadderEntry(
                            id="b1.grammar.conditionals-wish",
                            title="",
                            track=Track.GRAMMAR,
                            availability=ModuleAvailability.AVAILABLE,
                        ),
                    ),
                ),
            )
        )

    def module(self, module_id: str) -> Module:
        return self._modules[module_id]

    def lesson(self, module_id: str) -> Lesson:
        return self._lessons[module_id]

    def quiz(self, module_id: str) -> Quiz:
        return self._quizzes[module_id]

    def has_lesson(self, module_id: str) -> bool:
        return module_id in self._lessons

    def has_quiz(self, module_id: str) -> bool:
        return module_id in self._quizzes

    def is_available(self, module_id: str) -> bool:
        return module_id in self._available

    def placement(self) -> Placement:
        # The Today session never reads the placement bank; this fake only needs
        # to satisfy the CurriculumContent protocol.
        return Placement(items=())


class FakeProgress:
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

    async def mark_quiz_attempted(
        self, module_id: str, score: float, now: datetime
    ) -> ModuleProgress:
        current = self._items.get(module_id, ModuleProgress(module_id=module_id))
        updated = current.derive_status(lesson_read_at=now, quiz_attempted=True, now=now)
        self._items[module_id] = updated
        return updated


def _session(**overrides) -> BuildTodaySession:
    decks = FakeDeckRepository()
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    skills = FakeSkillItemRepository()
    content = FakeContent()
    progress = FakeProgress()
    profile = FakeLearnerProfileRepository()
    recommend = GetRecommendedModule(content, progress, profile)
    return BuildTodaySession(
        content,
        progress,
        decks,
        cards,
        logs,
        skills,
        recommend,
        FixedClock(NOW),
    )


async def _seed_deck(
    decks: FakeDeckRepository, cards: FakeCardRepository, words: list[str]
) -> None:
    deck = await decks.add(Deck(name="d", created_at=NOW))
    assert deck.id is not None
    await cards.add_many(
        [
            Card(
                deck_id=deck.id,
                word=word,
                translation="tr",
                fsrs=FsrsState(due=DUE_AT, state=2, stability=1.0),
            )
            for word in words
        ]
    )


async def _seed_future_deck(decks: FakeDeckRepository, cards: FakeCardRepository) -> None:
    deck = await decks.add(Deck(name="d", created_at=NOW))
    assert deck.id is not None
    await cards.add_many(
        [
            Card(
                deck_id=deck.id,
                word="apple",
                translation="tr",
                fsrs=FsrsState(due=NOW + timedelta(days=1), state=2, stability=1.0),
            )
        ]
    )


async def _future_skill(skills: FakeSkillItemRepository, skill: str) -> SkillItem:
    item = SkillItem.create(skill, "b1.grammar.articles", "q1", NOW)
    return await skills.add(
        item.with_fsrs(FsrsState(due=NOW + timedelta(days=1), state=2, stability=1.0))
    )


async def _due_skill(skills: FakeSkillItemRepository, skill: str) -> SkillItem:
    item = SkillItem.create(skill, "b1.grammar.articles", "q1", NOW)
    saved = await skills.add(item.with_fsrs(FsrsState(due=DUE_AT, state=2, stability=1.0)))
    return saved


async def _leech(skills: FakeSkillItemRepository, skill: str) -> SkillItem:
    item = SkillItem.create(skill, "b1.grammar.articles", "q1", NOW)
    return await skills.add(
        item.with_fsrs(
            FsrsState(due=NOW + timedelta(days=1), state=2, stability=1.0, lapses=LEECH_LAPSES)
        )
    )


async def test_session_empty_when_nothing_to_do():
    session = _session()
    await session._progress.save(
        ModuleProgress(module_id="b1.grammar.articles", status=ModuleStatus.COMPLETED)
    )
    await session._progress.save(
        ModuleProgress(module_id="b1.grammar.conditionals-wish", status=ModuleStatus.COMPLETED)
    )
    await _seed_future_deck(session._decks, session._cards)

    steps = await session.execute()

    assert steps == ()


async def test_session_full_ordering_and_payloads():
    session = _session()
    await _seed_deck(session._decks, session._cards, ["apple", "pear"])
    await _seed_deck(session._decks, session._cards, ["table"])
    await _due_skill(session._skills, "art.definite")
    leech = await _leech(session._skills, "cond.second")
    assert leech.id is not None
    await session._logs.add(ReviewLogEntry(card_id=1, rating=Rating.GOOD, reviewed_at=NOW))

    steps = await session.execute()

    assert [type(s).__name__ for s in steps] == [
        "ReviewStep",
        "ReadLessonStep",
        "ProduceStep",
        "FocusStep",
    ]
    review = steps[0]
    assert isinstance(review, ReviewStep)
    assert review.vocab_due == 3
    assert review.skill_due == 1
    learn = steps[1]
    assert isinstance(learn, ReadLessonStep)
    assert learn.module_id == "b1.grammar.articles"
    produce = steps[2]
    assert isinstance(produce, ProduceStep)
    assert produce.word == "apple"
    assert produce.card_id == 1
    focus = steps[3]
    assert isinstance(focus, FocusStep)
    assert [item.skill for item in focus.leeches] == ["cond.second"]


async def test_learn_step_is_take_quiz_when_lesson_read():
    session = _session()
    await session._progress.mark_lesson_read("b1.grammar.articles", NOW)
    await _seed_deck(session._decks, session._cards, ["apple"])

    steps = await session.execute()

    assert isinstance(steps[0], ReviewStep)
    learn = steps[1]
    assert isinstance(learn, TakeQuizStep)
    assert learn.module_id == "b1.grammar.articles"
    assert learn.items == 1


async def test_produce_step_omitted_without_recent_reviews():
    session = _session()
    await _seed_deck(session._decks, session._cards, ["apple"])

    steps = await session.execute()

    assert [type(s).__name__ for s in steps] == ["ReviewStep", "ReadLessonStep"]
    assert not any(isinstance(s, ProduceStep) for s in steps)


async def test_review_step_omitted_when_nothing_due():
    session = _session()
    await _future_skill(session._skills, "art.definite")

    steps = await session.execute()

    assert [type(s).__name__ for s in steps] == ["ReadLessonStep"]
    assert not any(isinstance(s, ReviewStep) for s in steps)


async def test_focus_step_omitted_without_leeches():
    session = _session()
    await _due_skill(session._skills, "art.definite")
    await session._logs.add(ReviewLogEntry(card_id=1, rating=Rating.GOOD, reviewed_at=NOW))
    await _seed_deck(session._decks, session._cards, ["apple"])

    steps = await session.execute()

    assert [type(s).__name__ for s in steps] == ["ReviewStep", "ReadLessonStep", "ProduceStep"]
    assert not any(isinstance(s, FocusStep) for s in steps)


async def test_learn_step_omitted_when_recommended_module_completed():
    session = _session()
    await session._progress.save(
        ModuleProgress(module_id="b1.grammar.articles", status=ModuleStatus.COMPLETED)
    )
    await session._progress.save(
        ModuleProgress(module_id="b1.grammar.conditionals-wish", status=ModuleStatus.COMPLETED)
    )
    await _seed_deck(session._decks, session._cards, ["apple"])

    steps = await session.execute()

    assert [type(s).__name__ for s in steps] == ["ReviewStep"]


class ModuleContent(FakeContent):
    """FakeContent whose recommended module carries pillar links."""

    def __init__(self, vocab: tuple[str, ...] = (), interview_topic: str | None = None) -> None:
        super().__init__()
        self._modules["b1.grammar.articles"] = Module(
            id="b1.grammar.articles",
            title="Articles",
            objectives=("Pick the article",),
            skills=("art.definite",),
            references=(),
            vocab=vocab,
            interview_topic=interview_topic,
        )


async def _session_with_content(content: FakeContent) -> BuildTodaySession:
    decks = FakeDeckRepository()
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    skills = FakeSkillItemRepository()
    progress = FakeProgress()
    profile = FakeLearnerProfileRepository()
    recommend = GetRecommendedModule(content, progress, profile)
    return BuildTodaySession(
        content,
        progress,
        decks,
        cards,
        logs,
        skills,
        recommend,
        FixedClock(NOW),
    )


async def test_produce_uses_module_vocab_link_when_declared():
    session = await _session_with_content(ModuleContent(vocab=("main",)))

    steps = await session.execute()

    produce = next(s for s in steps if isinstance(s, ProduceStep))
    assert produce.vocab_sections == ("main",)
    assert produce.interview_topic is None
    assert produce.word == ""


async def test_produce_uses_module_interview_topic_when_declared():
    session = await _session_with_content(ModuleContent(interview_topic="Frontend"))

    steps = await session.execute()

    produce = next(s for s in steps if isinstance(s, ProduceStep))
    assert produce.interview_topic == "Frontend"
    assert produce.vocab_sections == ()
    assert produce.word == ""


async def test_produce_prefers_vocab_link_over_interview_topic():
    session = await _session_with_content(ModuleContent(vocab=("main",), interview_topic="Backend"))

    steps = await session.execute()

    produce = next(s for s in steps if isinstance(s, ProduceStep))
    assert produce.vocab_sections == ("main",)
    assert produce.interview_topic is None
