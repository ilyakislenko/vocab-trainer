from sqlmodel import select

from vocab_api.application.ports.repositories import SentenceAttemptRepository
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.mappers import (
    sentence_attempt_from_row,
    sentence_attempt_to_row,
)
from vocab_api.infrastructure.persistence.tables import SentenceAttemptRow


class SqlSentenceAttemptRepository(SentenceAttemptRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, attempt: SentenceAttempt) -> SentenceAttempt:
        row = sentence_attempt_to_row(attempt)
        async with self._db.session() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return sentence_attempt_from_row(row)

    async def list_for_card(self, card_id: int) -> list[SentenceAttempt]:
        # SentenceAttemptRow.id is annotated as plain `int | None`; sqlmodel ships no
        # mypy plugin, so mypy sees that class attribute as a plain value instead of
        # the runtime InstrumentedAttribute that order_by() actually expects.
        statement = (
            select(SentenceAttemptRow)
            .where(SentenceAttemptRow.card_id == card_id)
            .order_by(SentenceAttemptRow.id)  # type: ignore[arg-type]
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [sentence_attempt_from_row(row) for row in rows]
