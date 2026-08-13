from dataclasses import dataclass
from datetime import datetime

from vocab_api.domain.shared.errors import EmptyDeckName


@dataclass(frozen=True, slots=True)
class Deck:
    name: str
    id: int | None = None
    created_at: datetime | None = None

    @staticmethod
    def create(name: str, now: datetime) -> "Deck":
        cleaned = name.strip()
        if not cleaned:
            raise EmptyDeckName()
        return Deck(name=cleaned, created_at=now)
