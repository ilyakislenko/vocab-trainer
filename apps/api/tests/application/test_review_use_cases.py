from datetime import timedelta

import pytest
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeReviewLogRepository,
    FixedClock,
)

from vocab_api.application.use_cases.review import GetReviewQueue, RecordReview
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.shared.errors import CardNotFound


class StubScheduler:
    def review(self, state: FsrsState, rating: Rating, now):
        return FsrsState(due=now + timedelta(days=int(rating)), stability=1.0, last_review=now)


async def test_queue_returns_due_cards_only():
    cards = FakeCardRepository()
    await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    queue = await GetReviewQueue(cards, FixedClock()).execute(deck_id=1, limit=10)
    assert [c.word for c in queue] == ["run"]


async def test_record_review_updates_card_and_logs():
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    (card,) = await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    assert card.id is not None
    updated = await RecordReview(cards, logs, StubScheduler(), FixedClock()).execute(
        card.id, Rating.GOOD
    )
    assert updated.fsrs.due == FIXED_NOW + timedelta(days=3)
    assert (await cards.get(card.id)).fsrs.stability == 1.0
    assert logs.entries[0].rating == Rating.GOOD


async def test_record_review_missing_card_raises():
    cards = FakeCardRepository()
    with pytest.raises(CardNotFound):
        await RecordReview(
            cards, FakeReviewLogRepository(cards), StubScheduler(), FixedClock()
        ).execute(999, Rating.GOOD)
