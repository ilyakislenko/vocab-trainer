from datetime import datetime

from sqlalchemy import func
from sqlmodel import select

from vocab_api.application.ports.repositories import CardRepository
from vocab_api.domain.card.card import Card
from vocab_api.domain.shared.errors import CardNotFound
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.mappers import card_from_row, card_to_row
from vocab_api.infrastructure.persistence.tables import CardRow


class SqlCardRepository(CardRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add_many(self, cards: list[Card]) -> list[Card]:
        rows = [card_to_row(card) for card in cards]
        async with self._db.session() as session:
            session.add_all(rows)
            await session.commit()
            for row in rows:
                await session.refresh(row)
        return [card_from_row(row) for row in rows]

    async def get(self, card_id: int) -> Card:
        async with self._db.session() as session:
            row = await session.get(CardRow, card_id)
        if row is None:
            raise CardNotFound(card_id)
        return card_from_row(row)

    async def save(self, card: Card) -> None:
        row = card_to_row(card)
        async with self._db.session() as session:
            await session.merge(row)
            await session.commit()

    async def due(self, deck_id: int, now: datetime, limit: int) -> list[Card]:
        # CardRow.fsrs_due is annotated as plain datetime; sqlmodel ships no mypy
        # plugin, so mypy sees that class attribute as a plain value instead of the
        # runtime InstrumentedAttribute that order_by() actually expects.
        statement = (
            select(CardRow)
            .where(CardRow.deck_id == deck_id, CardRow.fsrs_due <= now)
            .order_by(CardRow.fsrs_due)  # type: ignore[arg-type]
            .limit(limit)
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [card_from_row(row) for row in rows]

    async def count_due(self, deck_id: int, now: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(CardRow)
            .where(CardRow.deck_id == deck_id, CardRow.fsrs_due <= now)
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            return result.scalar_one()

    async def list_all(
        self, deck_id: int, limit: int, offset: int, section: str | None
    ) -> list[Card]:
        # CardRow.id is typed int | None; mypy sees it as a plain value instead
        # of the runtime InstrumentedAttribute order_by() expects.
        statement = select(CardRow).where(CardRow.deck_id == deck_id).order_by(CardRow.id)  # type: ignore[arg-type]
        if section is not None:
            statement = statement.where(CardRow.section == section)
        statement = statement.limit(limit).offset(offset)
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [card_from_row(row) for row in rows]

    async def by_words(self, deck_id: int, words: list[str]) -> list[Card]:
        lower = [w.lower() for w in words]
        statement = (
            select(CardRow)
            .where(CardRow.deck_id == deck_id, func.lower(CardRow.word).in_(lower))
            .order_by(CardRow.id)  # type: ignore[arg-type]  # same CardRow.id typing quirk as above
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [card_from_row(row) for row in rows]

    async def count_by_state(self, deck_id: int) -> dict[str, int]:
        statement = (
            select(CardRow.fsrs_state, func.count())
            .where(CardRow.deck_id == deck_id)
            .group_by(CardRow.fsrs_state)  # type: ignore[arg-type]  # same InstrumentedAttribute quirk
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.all()
        state_names = {0: "new", 1: "learning", 2: "review", 3: "relearning"}
        return {state_names.get(int(r[0]), "unknown"): int(r[1]) for r in rows}
