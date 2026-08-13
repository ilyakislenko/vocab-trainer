from datetime import UTC, datetime

import pytest

from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import EmptyDeckName

NOW = datetime(2026, 8, 13, tzinfo=UTC)


def test_create_trims_and_sets_created_at():
    deck = Deck.create("  Travel  ", NOW)
    assert deck.name == "Travel"
    assert deck.created_at == NOW
    assert deck.id is None


def test_blank_name_rejected():
    with pytest.raises(EmptyDeckName):
        Deck.create("   ", NOW)
