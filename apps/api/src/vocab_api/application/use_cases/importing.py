from dataclasses import dataclass

from vocab_api.application.importing.parser import Format, RowError, parse_words
from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, DeckRepository
from vocab_api.domain.card.card import Card


@dataclass(frozen=True, slots=True)
class ImportResult:
    imported: list[Card]
    errors: list[RowError]
    committed: bool


class ImportWords:
    def __init__(self, decks: DeckRepository, cards: CardRepository, clock: Clock) -> None:
        self._decks = decks
        self._cards = cards
        self._clock = clock

    async def execute(self, deck_id: int, raw: str, fmt: Format, dry_run: bool) -> ImportResult:
        await self._decks.get(deck_id)  # raises DeckNotFound
        now = self._clock.now()
        parsed, errors = parse_words(raw, fmt)
        cards = [
            Card.create(deck_id, row.word, row.translation, now, row.transcription)
            for row in parsed
        ]
        if dry_run:
            return ImportResult(imported=cards, errors=errors, committed=False)
        saved = await self._cards.add_many(cards)
        return ImportResult(imported=saved, errors=errors, committed=True)
