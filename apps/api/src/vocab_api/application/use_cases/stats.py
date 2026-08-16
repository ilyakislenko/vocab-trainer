from dataclasses import dataclass

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, ReviewLogRepository


@dataclass(frozen=True, slots=True)
class Stats:
    due_today: int
    total_reviews: int
    streak: int
    fsrs_new: int
    fsrs_learning: int
    fsrs_review: int
    fsrs_relearning: int
    activity: list[dict[str, int | str]]


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
        streak = await self._logs.streak(deck_id)
        activity = await self._logs.activity(deck_id, 7)
        by_state = await self._cards.count_by_state(deck_id)
        return Stats(
            due_today=due,
            total_reviews=reviews,
            streak=streak,
            fsrs_new=by_state.get("new", 0),
            fsrs_learning=by_state.get("learning", 0),
            fsrs_review=by_state.get("review", 0),
            fsrs_relearning=by_state.get("relearning", 0),
            activity=activity,
        )
