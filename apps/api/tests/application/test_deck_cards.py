from datetime import UTC, datetime

import pytest
from tests.conftest import FakeCardRepository, FakeDeckRepository, FixedClock

from vocab_api.application.use_cases.decks import CreateDeck, ListDeckCards
from vocab_api.domain.card.card import Card
from vocab_api.domain.shared.errors import DeckNotFound

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


async def _deck_with_cards() -> tuple[FakeDeckRepository, FakeCardRepository, int]:
    decks = FakeDeckRepository()
    cards = FakeCardRepository()
    deck_id = (await CreateDeck(decks, FixedClock(NOW)).execute("Travel")).id
    assert deck_id is not None
    await cards.add_many(
        [
            Card.create(deck_id, "run", "бежать", NOW, section="main"),
            Card.create(deck_id, "jump", "прыгать", NOW, section="main"),
            Card.create(deck_id, "train", "поезд", NOW, section="international"),
        ]
    )
    return decks, cards, deck_id


async def test_lists_all_cards_in_insertion_order():
    decks, cards, deck_id = await _deck_with_cards()
    result = await ListDeckCards(decks, cards).execute(deck_id, 100, 0)
    assert [c.word for c in result] == ["run", "jump", "train"]


async def test_paginates_and_offsets():
    decks, cards, deck_id = await _deck_with_cards()
    result = await ListDeckCards(decks, cards).execute(deck_id, 2, 0)
    assert [c.word for c in result] == ["run", "jump"]
    result = await ListDeckCards(decks, cards).execute(deck_id, 2, 2)
    assert [c.word for c in result] == ["train"]


async def test_filters_by_section():
    decks, cards, deck_id = await _deck_with_cards()
    result = await ListDeckCards(decks, cards).execute(deck_id, 100, 0, section="main")
    assert [c.word for c in result] == ["run", "jump"]


async def test_missing_deck_raises():
    decks, cards, _deck_id = await _deck_with_cards()
    with pytest.raises(DeckNotFound):
        await ListDeckCards(decks, cards).execute(999, 100, 0)
