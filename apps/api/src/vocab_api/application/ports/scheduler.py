from datetime import datetime
from typing import Protocol

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating


class Scheduler(Protocol):
    def review(self, state: FsrsState, rating: Rating, now: datetime) -> FsrsState: ...
