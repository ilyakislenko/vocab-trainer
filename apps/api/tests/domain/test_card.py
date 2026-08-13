from datetime import UTC, datetime

import pytest

from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.shared.errors import EmptyTranslation, EmptyWord

NOW = datetime(2026, 8, 13, tzinfo=UTC)


def test_create_builds_due_now_card():
    card = Card.create(deck_id=1, word=" run ", translation=" бежать ", now=NOW)
    assert card.word == "run"
    assert card.translation == "бежать"
    assert card.fsrs == FsrsState.new(NOW)
    assert card.deck_id == 1


def test_blank_word_or_translation_rejected():
    with pytest.raises(EmptyWord):
        Card.create(deck_id=1, word="", translation="x", now=NOW)
    with pytest.raises(EmptyTranslation):
        Card.create(deck_id=1, word="x", translation=" ", now=NOW)


def test_with_fsrs_returns_updated_copy():
    card = Card.create(deck_id=1, word="run", translation="бежать", now=NOW)
    later = FsrsState(due=NOW, state=2, stability=5.0)
    updated = card.with_fsrs(later)
    assert updated.fsrs == later
    assert card.fsrs != later  # original unchanged
