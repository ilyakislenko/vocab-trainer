from datetime import UTC, datetime

from vocab_api.domain.card.card import Card
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.domain.shared.errors import CardNotFound, DeckNotFound

FIXED_NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


class FixedClock:
    def __init__(self, now: datetime = FIXED_NOW) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakeDeckRepository:
    def __init__(self) -> None:
        self._items: dict[int, Deck] = {}
        self._seq = 0

    async def add(self, deck: Deck) -> Deck:
        self._seq += 1
        stored = Deck(id=self._seq, name=deck.name, created_at=deck.created_at)
        self._items[self._seq] = stored
        return stored

    async def get(self, deck_id: int) -> Deck:
        if deck_id not in self._items:
            raise DeckNotFound(deck_id)
        return self._items[deck_id]

    async def list(self) -> list[Deck]:
        return list(self._items.values())


class FakeCardRepository:
    def __init__(self) -> None:
        self._items: dict[int, Card] = {}
        self._seq = 0

    async def add_many(self, cards: list[Card]) -> list[Card]:
        saved: list[Card] = []
        for card in cards:
            self._seq += 1
            stored = Card(
                id=self._seq,
                deck_id=card.deck_id,
                word=card.word,
                translation=card.translation,
                fsrs=card.fsrs,
                transcription=card.transcription,
                notes=card.notes,
                created_at=card.created_at,
            )
            self._items[self._seq] = stored
            saved.append(stored)
        return saved

    async def get(self, card_id: int) -> Card:
        if card_id not in self._items:
            raise CardNotFound(card_id)
        return self._items[card_id]

    async def save(self, card: Card) -> None:
        assert card.id is not None
        self._items[card.id] = card

    async def due(self, deck_id: int, now: datetime, limit: int) -> list[Card]:
        due = [c for c in self._items.values() if c.deck_id == deck_id and c.fsrs.due <= now]
        due.sort(key=lambda c: c.fsrs.due)
        return due[:limit]

    async def count_due(self, deck_id: int, now: datetime) -> int:
        return len([c for c in self._items.values() if c.deck_id == deck_id and c.fsrs.due <= now])


class FakeReviewLogRepository:
    def __init__(self) -> None:
        self.entries: list[ReviewLogEntry] = []

    async def add(self, entry: ReviewLogEntry) -> None:
        self.entries.append(entry)

    async def count_reviews(self, deck_id: int) -> int:
        return len(self.entries)
