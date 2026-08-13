from dataclasses import dataclass
from datetime import datetime

from vocab_api.domain.practice.feedback import Feedback
from vocab_api.domain.shared.errors import EmptySentence


@dataclass(frozen=True, slots=True)
class SentenceAttempt:
    card_id: int
    sentence: str
    feedback: Feedback
    id: int | None = None
    created_at: datetime | None = None

    @staticmethod
    def create(
        card_id: int, sentence: str, feedback: Feedback, now: datetime
    ) -> "SentenceAttempt":
        cleaned = sentence.strip()
        if not cleaned:
            raise EmptySentence()
        return SentenceAttempt(
            card_id=card_id, sentence=cleaned, feedback=feedback, created_at=now
        )
