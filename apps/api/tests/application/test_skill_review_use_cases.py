from datetime import UTC, datetime, timedelta

import pytest
from tests.conftest import (
    FakeSkillItemRepository,
    FixedClock,
    StubScheduler,
)

from vocab_api.application.use_cases.skills import (
    GetFocusLeeches,
    GetSkillReviewQueue,
    RecordSkillReview,
)
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.curriculum.quiz import Quiz, QuizItem, QuizItemType
from vocab_api.domain.curriculum.skill_item import LEECH_LAPSES, SkillItem
from vocab_api.domain.shared.errors import SkillItemNotFound

NOW = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)

QUIZ = Quiz(
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
            prompt="She plays ___ violin.",
            explanation="Musical instruments take 'the'.",
            answers=("the",),
        ),
    ),
)


class FakeContent:
    def quiz(self, module_id: str) -> Quiz:
        assert module_id == "b1.grammar.articles"
        return QUIZ


def _item(skill: str, due: datetime, lapses: int = 0) -> SkillItem:
    return SkillItem(
        skill=skill,
        module_id="b1.grammar.articles",
        source_item_id="q1" if skill == "art.indefinite" else "q2",
        fsrs=FsrsState(due=due, state=2, stability=1.0, lapses=lapses),
        id=len(skill),
    )


async def test_queue_returns_due_skills_enriched_with_source_item():
    skills = FakeSkillItemRepository()
    await skills.add(_item("art.indefinite", due=NOW))
    await skills.add(_item("art.definite", due=NOW + timedelta(days=10)))

    queue = await GetSkillReviewQueue(skills, FakeContent(), FixedClock(NOW)).execute(10)

    assert [q.skill for q in queue] == ["art.indefinite"]
    review = queue[0]
    assert review.type is QuizItemType.MCQ
    assert review.prompt == "Pick the article"
    assert review.answers == ("an",)
    assert review.explanation == "Use 'an' before a vowel sound."
    assert review.is_leech is False


async def test_queue_limit_bounds_results():
    skills = FakeSkillItemRepository()
    await skills.add(_item("art.indefinite", due=NOW))
    await skills.add(_item("art.definite", due=NOW))

    queue = await GetSkillReviewQueue(skills, FakeContent(), FixedClock(NOW)).execute(1)

    assert len(queue) == 1


async def test_queue_skips_items_with_missing_source():
    skills = FakeSkillItemRepository()
    await skills.add(SkillItem(skill="ghost", module_id="b1.grammar.articles",
                               source_item_id="missing", fsrs=FsrsState(due=NOW)))

    queue = await GetSkillReviewQueue(skills, FakeContent(), FixedClock(NOW)).execute(10)

    assert queue == []


async def test_record_review_advances_fsrs():
    skills = FakeSkillItemRepository()
    created = await skills.add(_item("art.indefinite", due=NOW, lapses=1))

    updated = await RecordSkillReview(skills, StubScheduler(), FixedClock(NOW)).execute(
        created.id or 0, Rating.GOOD
    )

    assert updated.fsrs.due == NOW + timedelta(days=3)
    assert updated.fsrs.last_review == NOW
    assert updated.fsrs.lapses == 1  # Good rating does not add a lapse


async def test_record_review_again_on_review_state_counts_lapse():
    skills = FakeSkillItemRepository()
    created = await skills.add(_item("art.indefinite", due=NOW, lapses=1))

    updated = await RecordSkillReview(skills, StubScheduler(), FixedClock(NOW)).execute(
        created.id or 0, Rating.AGAIN
    )

    assert updated.fsrs.lapses == 2


async def test_record_review_again_while_relearning_also_counts_lapse():
    skills = FakeSkillItemRepository()
    created = await skills.add(
        SkillItem(
            skill="art.indefinite",
            module_id="b1.grammar.articles",
            source_item_id="q1",
            fsrs=FsrsState(due=NOW, state=3, stability=1.0, lapses=2),
        )
    )

    updated = await RecordSkillReview(skills, StubScheduler(), FixedClock(NOW)).execute(
        created.id or 0, Rating.AGAIN
    )

    # A relapse while relearning counts too, so a skill you keep bombing in one
    # session still reaches the Focus list promptly. Only initial-learning
    # misses (state 0/1) are exempt.
    assert updated.fsrs.lapses == 3


async def test_record_review_missing_item_raises():
    skills = FakeSkillItemRepository()
    with pytest.raises(SkillItemNotFound):
        await RecordSkillReview(skills, StubScheduler(), FixedClock(NOW)).execute(999, Rating.GOOD)


async def test_focus_returns_leeches_weakest_first():
    skills = FakeSkillItemRepository()
    await skills.add(_item("art.indefinite", due=NOW, lapses=LEECH_LAPSES))
    await skills.add(_item("art.definite", due=NOW, lapses=LEECH_LAPSES + 2))
    await skills.add(_item("art.zero", due=NOW, lapses=1))

    focus = await GetFocusLeeches(skills).execute(3)

    assert [f.skill for f in focus] == ["art.definite", "art.indefinite"]
    assert all(f.is_leech for f in focus)


async def test_focus_limit_applies():
    skills = FakeSkillItemRepository()
    await skills.add(_item("art.indefinite", due=NOW, lapses=LEECH_LAPSES))
    await skills.add(_item("art.definite", due=NOW, lapses=LEECH_LAPSES))

    focus = await GetFocusLeeches(skills).execute(1)

    assert len(focus) == 1