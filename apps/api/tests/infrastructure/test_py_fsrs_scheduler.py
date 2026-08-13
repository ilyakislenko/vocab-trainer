from datetime import UTC, datetime

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.infrastructure.scheduling.py_fsrs_scheduler import PyFsrsScheduler

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def test_reviewing_new_card_pushes_due_into_the_future_and_records_stability():
    scheduler = PyFsrsScheduler()
    new_state = FsrsState.new(NOW)
    updated = scheduler.review(new_state, Rating.GOOD, NOW)
    assert updated.due > NOW
    assert updated.stability is not None
    assert updated.last_review == NOW


def test_again_schedules_sooner_than_easy():
    scheduler = PyFsrsScheduler()
    again = scheduler.review(FsrsState.new(NOW), Rating.AGAIN, NOW)
    easy = scheduler.review(FsrsState.new(NOW), Rating.EASY, NOW)
    assert again.due < easy.due
