from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeReviewLogRepository,
    FixedClock,
)

from vocab_api.application.use_cases.stats import GetStats
from vocab_api.domain.card.card import Card


async def test_stats_counts_due_and_reviews():
    cards, logs = FakeCardRepository(), FakeReviewLogRepository()
    await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    stats = await GetStats(cards, logs, FixedClock()).execute(deck_id=1)
    assert stats.due_today == 1
    assert stats.total_reviews == 0
