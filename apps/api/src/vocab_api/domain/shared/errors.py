class DomainError(Exception):
    """Base class for domain rule violations."""


class EmptyDeckName(DomainError):
    def __init__(self) -> None:
        super().__init__("Deck name must not be empty.")


class EmptyWord(DomainError):
    def __init__(self) -> None:
        super().__init__("Word must not be empty.")


class EmptyTranslation(DomainError):
    def __init__(self) -> None:
        super().__init__("Translation must not be empty.")


class EmptySentence(DomainError):
    def __init__(self) -> None:
        super().__init__("Sentence must not be empty.")


class EmptyTopic(DomainError):
    def __init__(self) -> None:
        super().__init__("Topic must not be empty.")


class DeckNotFound(DomainError):
    def __init__(self, deck_id: int) -> None:
        super().__init__(f"deck {deck_id} not found")
        self.deck_id = deck_id


class CardNotFound(DomainError):
    def __init__(self, card_id: int) -> None:
        super().__init__(f"card {card_id} not found")
        self.card_id = card_id


class CurriculumModuleNotFound(DomainError):
    def __init__(self, module_id: str) -> None:
        super().__init__(f"module {module_id!r} not found")
        self.module_id = module_id


class CurriculumLessonNotFound(DomainError):
    def __init__(self, module_id: str) -> None:
        super().__init__(f"lesson for module {module_id!r} not found")
        self.module_id = module_id


class ContentValidationError(DomainError):
    """The content bundle failed validation; the app must not serve it."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"curriculum content invalid: {reason}")
        self.reason = reason
