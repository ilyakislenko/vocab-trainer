from datetime import datetime, timedelta

import pytest
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeReviewLogRepository,
    FixedClock,
)

from vocab_api.application.use_cases.review import (
    GetReviewQueue,
    GetReviewSummary,
    RecordReview,
    new_card_allowance,
)
from vocab_api.domain.card.card import NEW_CARDS_PER_DAY, Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.domain.shared.errors import CardNotFound


class StubScheduler:
    def review(self, state: FsrsState, rating: Rating, now):
        return FsrsState(
            due=now + timedelta(days=int(rating)),
            state=2,
            stability=1.0,
            last_review=now,
        )


def new_card(deck_id: int, word: str) -> Card:
    return Card.create(deck_id, word, f"перевод {word}", FIXED_NOW)


def due_card(deck_id: int, word: str, due: datetime | None = None) -> Card:
    return Card(
        deck_id=deck_id,
        word=word,
        translation=f"перевод {word}",
        fsrs=FsrsState(due=FIXED_NOW if due is None else due, state=2, stability=1.0),
    )


async def test_queue_mixes_all_due_with_capped_new():
    cards = FakeCardRepository()
    await cards.add_many(
        [due_card(1, "old-a"), due_card(1, "old-b"), due_card(1, "old-c")]
        + [new_card(1, f"fresh-{i}") for i in range(100)]
    )
    queue = await GetReviewQueue(cards, FixedClock()).execute(deck_id=1, limit=50)
    assert len(queue) == 3 + NEW_CARDS_PER_DAY
    assert [c.word for c in queue[:3]] == ["old-a", "old-b", "old-c"]
    assert [c.word for c in queue[3:]] == [f"fresh-{i}" for i in range(NEW_CARDS_PER_DAY)]


async def test_queue_new_batch_respects_limit():
    cards = FakeCardRepository()
    await cards.add_many([new_card(1, "a"), new_card(1, "b"), new_card(1, "c")])
    queue = await GetReviewQueue(cards, FixedClock()).execute(deck_id=1, limit=2)
    assert [c.word for c in queue] == ["a", "b"]


async def test_queue_new_budget_shrinks_after_introductions():
    cards = FakeCardRepository()
    await cards.add_many([due_card(1, "due")])
    await cards.add_many(
        [
            Card(
                deck_id=1,
                word=f"n-{i}",
                translation="перевод",
                fsrs=FsrsState.new(FIXED_NOW),
                introduced_at=FIXED_NOW,
            )
            for i in range(30)
        ]
    )
    queue = await GetReviewQueue(cards, FixedClock()).execute(deck_id=1, limit=50)
    # 30 already introduced today: allowance is 0, so no new cards, only the due one.
    assert [c.word for c in queue] == ["due"]


async def test_first_review_stamps_introduced_at_and_drops_from_new():
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    (card,) = await cards.add_many([new_card(1, "run")])
    assert card.id is not None
    await RecordReview(cards, logs, StubScheduler(), FixedClock()).execute(card.id, Rating.GOOD)
    stored = await cards.get(card.id)
    assert stored.introduced_at == FIXED_NOW
    assert await cards.count_new(1) == 0
    assert await cards.count_introduced_today(1, FIXED_NOW.replace(hour=0)) == 1
    assert await cards.count_due(1, FIXED_NOW) == 0
    assert await new_card_allowance(cards, 1, FIXED_NOW) == NEW_CARDS_PER_DAY - 1


async def test_record_review_missing_card_raises():
    cards = FakeCardRepository()
    with pytest.raises(CardNotFound):
        await RecordReview(
            cards, FakeReviewLogRepository(cards), StubScheduler(), FixedClock()
        ).execute(999, Rating.GOOD)


async def test_review_summary_reports_next_due_and_reviewed_today():
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    later = FIXED_NOW + timedelta(days=2)
    (card, _) = await cards.add_many(
        [due_card(1, "future", due=later), new_card(1, "fresh")]
    )
    assert card.id is not None
    logs.entries.append(ReviewLogEntry(card_id=card.id, rating=Rating.GOOD, reviewed_at=FIXED_NOW))
    summary = await GetReviewSummary(cards, logs, FixedClock()).execute(deck_id=1)
    assert summary.next_due == later
    assert summary.reviewed_today == 1


async def test_review_summary_next_due_none_when_nothing_future():
    cards = FakeCardRepository()
    await cards.add_many([due_card(1, "overdue")])
    summary = await GetReviewSummary(cards, FakeReviewLogRepository(cards), FixedClock()).execute(1)
    assert summary.next_due is None
    assert summary.reviewed_today == 0