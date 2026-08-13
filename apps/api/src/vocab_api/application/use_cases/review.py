from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, ReviewLogRepository
from vocab_api.application.ports.scheduler import Scheduler
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.review.review_log import ReviewLogEntry


class GetReviewQueue:
    def __init__(self, cards: CardRepository, clock: Clock) -> None:
        self._cards = cards
        self._clock = clock

    async def execute(self, deck_id: int, limit: int) -> list[Card]:
        return await self._cards.due(deck_id, self._clock.now(), limit)


class RecordReview:
    def __init__(
        self,
        cards: CardRepository,
        logs: ReviewLogRepository,
        scheduler: Scheduler,
        clock: Clock,
    ) -> None:
        self._cards = cards
        self._logs = logs
        self._scheduler = scheduler
        self._clock = clock

    async def execute(self, card_id: int, rating: Rating) -> Card:
        now = self._clock.now()
        card = await self._cards.get(card_id)  # raises CardNotFound
        updated = card.with_fsrs(self._scheduler.review(card.fsrs, rating, now))
        await self._cards.save(updated)
        await self._logs.add(ReviewLogEntry(card_id=card_id, rating=rating, reviewed_at=now))
        return updated
