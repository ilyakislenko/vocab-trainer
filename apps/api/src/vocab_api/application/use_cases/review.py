from dataclasses import dataclass, replace
from datetime import datetime

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, ReviewLogRepository
from vocab_api.application.ports.scheduler import Scheduler
from vocab_api.domain.card.card import NEW_CARDS_PER_DAY, Card
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.review.review_log import ReviewLogEntry


def start_of_day(now: datetime) -> datetime:
    """UTC midnight for the given instant — the app's day boundary."""
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


async def new_card_allowance(cards: CardRepository, deck_id: int, now: datetime) -> int:
    """How many brand-new cards remain today: cap minus what was already introduced."""
    introduced = await cards.count_introduced_today(deck_id, start_of_day(now))
    return max(0, NEW_CARDS_PER_DAY - introduced)


@dataclass(frozen=True, slots=True)
class ReviewSummary:
    next_due: datetime | None
    reviewed_today: int


class GetReviewSummary:
    """Facts for the review screen: when the next card is due and how many cards
    were already reviewed today (drives the honest 'Done' screen)."""

    def __init__(self, cards: CardRepository, logs: ReviewLogRepository, clock: Clock) -> None:
        self._cards = cards
        self._logs = logs
        self._clock = clock

    async def execute(self, deck_id: int) -> ReviewSummary:
        now = self._clock.now()
        next_due = await self._cards.soonest_due(deck_id, now)
        reviewed_today = await self._logs.count_reviews_on(deck_id, start_of_day(now))
        return ReviewSummary(next_due=next_due, reviewed_today=reviewed_today)


class GetReviewQueue:
    def __init__(self, cards: CardRepository, clock: Clock) -> None:
        self._cards = cards
        self._clock = clock

    async def execute(self, deck_id: int, limit: int) -> list[Card]:
        """The daily plan: all genuinely-due cards plus today's new-card budget."""
        now = self._clock.now()
        due = await self._cards.due(deck_id, now)
        allowance = await new_card_allowance(self._cards, deck_id, now)
        fresh = await self._cards.new_cards(deck_id, min(allowance, limit))
        return due + fresh


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
        if card.fsrs.state == 0:
            # First review of a brand-new card: mark when it entered the loop so
            # the daily new-card budget can count it.
            updated = replace(updated, introduced_at=now)
        await self._cards.save(updated)
        await self._logs.add(ReviewLogEntry(card_id=card_id, rating=rating, reviewed_at=now))
        return updated