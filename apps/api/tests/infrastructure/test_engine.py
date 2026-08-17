from sqlmodel import select

from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.tables import DeckRow


async def test_init_creates_tables_and_roundtrips_a_row():
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    async with db.session() as session:
        session.add(DeckRow(name="Travel"))
        await session.commit()
    async with db.session() as session:
        result = await session.execute(select(DeckRow))
        decks = result.scalars().all()
    await db.dispose()
    assert [d.name for d in decks] == ["Travel"]
