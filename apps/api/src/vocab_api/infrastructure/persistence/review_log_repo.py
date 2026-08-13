from sqlmodel import select

from vocab_api.application.ports.repositories import ReviewLogRepository
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.tables import CardRow, ReviewLogRow


class SqlReviewLogRepository(ReviewLogRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, entry: ReviewLogEntry) -> None:
        row = ReviewLogRow(
            card_id=entry.card_id,
            rating=int(entry.rating),
            reviewed_at=entry.reviewed_at,
        )
        async with self._db.session() as session:
            session.add(row)
            await session.commit()

    async def count_reviews(self, deck_id: int) -> int:
        # CardRow.id is annotated as plain `int | None`; sqlmodel ships no mypy
        # plugin, so mypy sees that class attribute as a plain value instead of the
        # runtime InstrumentedAttribute that join() actually expects.
        statement = (
            select(ReviewLogRow)
            .join(CardRow, CardRow.id == ReviewLogRow.card_id)  # type: ignore[arg-type]
            .where(CardRow.deck_id == deck_id)
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            return len(result.scalars().all())
