import pytest
from tests.conftest import FakeDeckRepository, FixedClock

from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.domain.shared.errors import EmptyDeckName


async def test_create_deck_persists_and_returns_with_id():
    repo = FakeDeckRepository()
    deck = await CreateDeck(repo, FixedClock()).execute(" Travel ")
    assert deck.id == 1
    assert deck.name == "Travel"
    assert await ListDecks(repo).execute() == [deck]


async def test_create_deck_rejects_blank():
    with pytest.raises(EmptyDeckName):
        await CreateDeck(FakeDeckRepository(), FixedClock()).execute("  ")
