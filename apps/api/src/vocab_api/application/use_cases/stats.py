from dataclasses import dataclass

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, ReviewLogRepository


@dataclass(frozen=True, slots=True)
class Stats:
    due_today: int
    total_reviews: int


class GetStats:
    def __init__(
        self, cards: CardRepository, logs: ReviewLogRepository, clock: Clock
    ) -> None:
        self._cards = cards
        self._logs = logs
        self._clock = clock

    async def execute(self, deck_id: int) -> Stats:
        due = await self._cards.count_due(deck_id, self._clock.now())
        reviews = await self._logs.count_reviews(deck_id)
        return Stats(due_today=due, total_reviews=reviews)
