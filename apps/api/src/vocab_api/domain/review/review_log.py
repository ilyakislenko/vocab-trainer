from dataclasses import dataclass
from datetime import datetime

from vocab_api.domain.card.rating import Rating


@dataclass(frozen=True, slots=True)
class ReviewLogEntry:
    card_id: int
    rating: Rating
    reviewed_at: datetime
