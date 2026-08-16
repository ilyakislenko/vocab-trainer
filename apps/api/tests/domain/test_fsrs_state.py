from datetime import UTC, datetime

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating


def test_new_state_is_due_now_and_new():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    state = FsrsState.new(now)
    assert state.due == now
    assert state.state == 0
    assert state.step == 0
    assert state.stability is None
    assert state.last_review is None


def test_ratings_map_to_fsrs_values():
    assert (Rating.AGAIN, Rating.HARD, Rating.GOOD, Rating.EASY) == (1, 2, 3, 4)
