class DomainError(Exception):
    """Base class for domain rule violations."""


class EmptyDeckName(DomainError):
    pass


class EmptyWord(DomainError):
    pass


class EmptyTranslation(DomainError):
    pass


class DeckNotFound(DomainError):
    def __init__(self, deck_id: int) -> None:
        super().__init__(f"deck {deck_id} not found")
        self.deck_id = deck_id


class CardNotFound(DomainError):
    def __init__(self, card_id: int) -> None:
        super().__init__(f"card {card_id} not found")
        self.card_id = card_id
