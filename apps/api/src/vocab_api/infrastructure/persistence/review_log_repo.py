from datetime import datetime, timedelta

from sqlalchemy import func
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
            select(func.count())
            .select_from(ReviewLogRow)
            .join(CardRow, CardRow.id == ReviewLogRow.card_id)  # type: ignore[arg-type]
            .where(CardRow.deck_id == deck_id)
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            return result.scalar_one()

    async def streak(self, deck_id: int) -> int:
        # Count consecutive days ending today with at least one review.
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(func.date(ReviewLogRow.reviewed_at))
            .join(CardRow, CardRow.id == ReviewLogRow.card_id)  # type: ignore[arg-type]
            .where(CardRow.deck_id == deck_id)
            .group_by(func.date(ReviewLogRow.reviewed_at))
            .order_by(func.date(ReviewLogRow.reviewed_at).desc())
        )
        async with self._db.session() as session:
            result = await session.execute(stmt)
            dates = [str(r[0]) for r in result.all()]
        if not dates:
            return 0
        streak = 0
        check = today
        for d in dates:
            expected = check.strftime("%Y-%m-%d")
            yesterday = (check - timedelta(days=1)).strftime("%Y-%m-%d")
            if d == expected or d == yesterday:
                streak += 1
                check -= timedelta(days=1)
            else:
                break
        return streak

    async def activity(self, deck_id: int, days: int) -> list[dict[str, int | str]]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(func.date(ReviewLogRow.reviewed_at).label("day"), func.count().label("count"))
            .join(CardRow, CardRow.id == ReviewLogRow.card_id)  # type: ignore[arg-type]
            .where(
                CardRow.deck_id == deck_id,
                ReviewLogRow.reviewed_at >= today - timedelta(days=days),
            )
            .group_by(func.date(ReviewLogRow.reviewed_at))
            .order_by(func.date(ReviewLogRow.reviewed_at))
        )
        async with self._db.session() as session:
            result = await session.execute(stmt)
            return [{"date": str(r[0]), "count": int(r[1])} for r in result.all()]
