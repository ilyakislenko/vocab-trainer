from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, DeckRepository
from vocab_api.domain.card.card import Card
from vocab_api.domain.deck.deck import Deck


class CreateDeck:
    def __init__(self, decks: DeckRepository, clock: Clock) -> None:
        self._decks = decks
        self._clock = clock

    async def execute(self, name: str) -> Deck:
        return await self._decks.add(Deck.create(name, self._clock.now()))


class ListDecks:
    def __init__(self, decks: DeckRepository) -> None:
        self._decks = decks

    async def execute(self) -> list[Deck]:
        return await self._decks.list()


class ListDeckCards:
    def __init__(self, decks: DeckRepository, cards: CardRepository) -> None:
        self._decks = decks
        self._cards = cards

    async def execute(
        self, deck_id: int, limit: int, offset: int, section: str | None = None
    ) -> list[Card]:
        await self._decks.get(deck_id)  # raises DeckNotFound
        return await self._cards.list_all(deck_id, limit, offset, section)
