from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeReviewLogRepository,
    FixedClock,
)

from vocab_api.application.use_cases.stats import GetStats
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.review.review_log import ReviewLogEntry


async def test_stats_counts_due_and_reviews():
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    stats = await GetStats(cards, logs, FixedClock()).execute(deck_id=1)
    assert stats.due_today == 1
    assert stats.total_reviews == 0


async def test_stats_total_reviews_are_scoped_to_the_requested_deck():
    # Regression for M4: the fake used to ignore deck_id entirely (len(entries)),
    # so a review logged against another deck would leak into this deck's count.
    cards = FakeCardRepository()
    logs = FakeReviewLogRepository(cards)
    (card_a,) = await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    (card_b,) = await cards.add_many([Card.create(2, "walk", "идти", FIXED_NOW)])
    assert card_a.id is not None
    assert card_b.id is not None
    await logs.add(ReviewLogEntry(card_id=card_a.id, rating=Rating.GOOD, reviewed_at=FIXED_NOW))
    await logs.add(ReviewLogEntry(card_id=card_b.id, rating=Rating.GOOD, reviewed_at=FIXED_NOW))
    await logs.add(ReviewLogEntry(card_id=card_b.id, rating=Rating.EASY, reviewed_at=FIXED_NOW))

    assert await logs.count_reviews(deck_id=1) == 1
    assert await logs.count_reviews(deck_id=2) == 2
