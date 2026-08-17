from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest

from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.domain.shared.errors import CardNotFound
from vocab_api.infrastructure.persistence.card_repo import SqlCardRepository
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.review_log_repo import SqlReviewLogRepository

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


@pytest.fixture
async def db() -> AsyncIterator[Database]:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.init()
    yield database
    await database.dispose()


async def test_add_many_assigns_ids_and_due_filters_and_orders(db: Database):
    repo = SqlCardRepository(db)
    future = Card.create(1, "later", "позже", NOW).with_fsrs(
        FsrsState(due=NOW + timedelta(days=1), state=2, stability=1.0)
    )
    due_now = Card.create(1, "now", "сейчас", NOW).with_fsrs(
        FsrsState(due=NOW, state=1, stability=1.0)
    )
    fresh = Card.create(1, "fresh", "новое", NOW)
    saved = await repo.add_many([future, due_now, fresh])
    assert all(c.id is not None for c in saved)

    # Brand-new cards are not "due" — they enter the loop via the daily budget.
    due = await repo.due(deck_id=1, now=NOW)
    assert [c.word for c in due] == ["now"]
    assert await repo.count_due(deck_id=1, now=NOW) == 1
    assert await repo.count_new(deck_id=1) == 1


async def test_new_cards_in_creation_order_and_count_introduced_today(db: Database):
    repo = SqlCardRepository(db)
    fresh = Card.create(1, "jump", "прыгать", NOW)
    introduced = Card(
        deck_id=1,
        word="run",
        translation="бежать",
        fsrs=FsrsState(due=NOW + timedelta(days=1), state=1, stability=1.0),
        introduced_at=NOW,
    )
    await repo.add_many([introduced, fresh])
    assert [c.word for c in await repo.new_cards(deck_id=1, limit=10)] == ["jump"]
    assert await repo.count_new(deck_id=1) == 1
    assert await repo.count_introduced_today(1, NOW.replace(hour=0)) == 1
    assert await repo.soonest_due(1, NOW) == NOW + timedelta(days=1)


async def test_save_persists_updated_fsrs_and_get_missing_raises(db: Database):
    repo = SqlCardRepository(db)
    (card,) = await repo.add_many([Card.create(1, "run", "бежать", NOW)])
    assert card.id is not None
    await repo.save(card.with_fsrs(FsrsState(due=NOW + timedelta(days=3), stability=9.0)))
    reloaded = await repo.get(card.id)
    assert reloaded.fsrs.stability == 9.0
    with pytest.raises(CardNotFound):
        await repo.get(999)


async def test_review_log_add_and_count(db: Database):
    cards = SqlCardRepository(db)
    (card,) = await cards.add_many([Card.create(1, "run", "бежать", NOW)])
    assert card.id is not None
    logs = SqlReviewLogRepository(db)
    await logs.add(ReviewLogEntry(card_id=card.id, rating=Rating.GOOD, reviewed_at=NOW))
    assert await logs.count_reviews(deck_id=1) == 1
