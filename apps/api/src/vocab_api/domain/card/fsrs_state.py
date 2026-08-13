from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FsrsState:
    due: datetime
    state: int = 1  # 1=Learning, 2=Review, 3=Relearning
    step: int | None = 0
    stability: float | None = None
    difficulty: float | None = None
    last_review: datetime | None = None

    @staticmethod
    def new(now: datetime) -> "FsrsState":
        return FsrsState(due=now)
