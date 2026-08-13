from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import DeckRepository
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
