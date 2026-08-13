from datetime import UTC, datetime

import pytest

from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import DeckNotFound
from vocab_api.infrastructure.persistence.deck_repo import SqlDeckRepository
from vocab_api.infrastructure.persistence.engine import Database

NOW = datetime(2026, 8, 13, tzinfo=UTC)


async def _repo() -> SqlDeckRepository:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    return SqlDeckRepository(db)


async def test_add_assigns_id_and_get_returns_it():
    repo = await _repo()
    saved = await repo.add(Deck.create("Travel", NOW))
    assert saved.id is not None
    fetched = await repo.get(saved.id)
    assert fetched.name == "Travel"


async def test_get_missing_raises():
    repo = await _repo()
    with pytest.raises(DeckNotFound):
        await repo.get(999)
