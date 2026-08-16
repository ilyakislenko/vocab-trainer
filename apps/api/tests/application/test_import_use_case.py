import pytest
from tests.conftest import FakeCardRepository, FakeDeckRepository, FixedClock

from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import DeckNotFound


async def _deck(repo: FakeDeckRepository) -> int:
    saved = await repo.add(Deck.create("Travel", FixedClock().now()))
    assert saved.id is not None
    return saved.id


async def test_dry_run_parses_without_persisting():
    decks, cards = FakeDeckRepository(), FakeCardRepository()
    deck_id = await _deck(decks)
    result = await ImportWords(decks, cards, FixedClock()).execute(
        deck_id, "run,rʌn,бежать", "csv", dry_run=True
    )
    assert result.committed is False
    assert [c.word for c in result.imported] == ["run"]
    assert await cards.count_due(deck_id, FixedClock().now()) == 0


async def test_commit_persists_valid_rows_and_returns_errors():
    decks, cards = FakeDeckRepository(), FakeCardRepository()
    deck_id = await _deck(decks)
    result = await ImportWords(decks, cards, FixedClock()).execute(
        deck_id, ",ipa,бежать\njump,dʒʌmp,прыгать", "csv", dry_run=False
    )
    assert result.committed is True
    assert [c.word for c in result.imported] == ["jump"]
    assert result.imported[0].id is not None
    assert [e.reason for e in result.errors] == ["empty word"]


async def test_missing_deck_raises():
    with pytest.raises(DeckNotFound):
        await ImportWords(FakeDeckRepository(), FakeCardRepository(), FixedClock()).execute(
            999, "run,бежать", "csv", dry_run=True
        )


async def test_commit_tags_rows_with_section():
    decks, cards = FakeDeckRepository(), FakeCardRepository()
    deck_id = await _deck(decks)
    result = await ImportWords(decks, cards, FixedClock()).execute(
        deck_id, "run,rʌn,бежать", "csv", dry_run=False, section="main"
    )
    assert result.imported[0].section == "main"
    stored = await cards.get(result.imported[0].id or 0)
    assert stored.section == "main"
