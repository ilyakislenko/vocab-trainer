from sqlmodel import select

from vocab_api.application.ports.repositories import DeckRepository
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import DeckNotFound
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.mappers import deck_from_row, deck_to_row
from vocab_api.infrastructure.persistence.tables import DeckRow


class SqlDeckRepository(DeckRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, deck: Deck) -> Deck:
        row = deck_to_row(deck)
        async with self._db.session() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return deck_from_row(row)

    async def get(self, deck_id: int) -> Deck:
        async with self._db.session() as session:
            row = await session.get(DeckRow, deck_id)
        if row is None:
            raise DeckNotFound(deck_id)
        return deck_from_row(row)

    async def list(self) -> list[Deck]:
        async with self._db.session() as session:
            # DeckRow.id is annotated `int | None`; sqlmodel ships no mypy plugin, so
            # mypy sees the class attribute as that plain type instead of the runtime
            # InstrumentedAttribute order_by() actually expects.
            result = await session.execute(
                select(DeckRow).order_by(DeckRow.id)  # type: ignore[arg-type]
            )
            rows = result.scalars().all()
        return [deck_from_row(row) for row in rows]
