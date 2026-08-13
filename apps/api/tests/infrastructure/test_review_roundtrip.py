from datetime import UTC, datetime, timedelta

from vocab_api.application.ports.clock import Clock
from vocab_api.application.use_cases.review import RecordReview
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.rating import Rating
from vocab_api.infrastructure.persistence.card_repo import SqlCardRepository
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.review_log_repo import SqlReviewLogRepository
from vocab_api.infrastructure.scheduling.py_fsrs_scheduler import PyFsrsScheduler

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


class _StepClock(Clock):
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


async def _db() -> Database:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    return db


async def test_second_review_survives_sqlite_naive_datetime_round_trip():
    # Regression for C1: SQLite drops tzinfo, so fsrs_due/fsrs_last_review come back
    # naive from the DB. The second review feeds that naive last_review into py-fsrs
    # alongside a tz-aware `now`, which used to raise TypeError before the mappers
    # re-attached UTC on read.
    db = await _db()
    cards = SqlCardRepository(db)
    logs = SqlReviewLogRepository(db)
    scheduler = PyFsrsScheduler()

    (card,) = await cards.add_many([Card.create(1, "run", "бежать", NOW)])
    assert card.id is not None

    first_review = RecordReview(cards, logs, scheduler, _StepClock(NOW))
    await first_review.execute(card.id, Rating.GOOD)

    reloaded = await cards.get(card.id)
    assert reloaded.fsrs.last_review is not None

    second_now = NOW + timedelta(days=1)
    second_review = RecordReview(cards, logs, scheduler, _StepClock(second_now))
    result = await second_review.execute(card.id, Rating.GOOD)

    assert result.fsrs.last_review == second_now
    assert await logs.count_reviews(deck_id=1) == 2
