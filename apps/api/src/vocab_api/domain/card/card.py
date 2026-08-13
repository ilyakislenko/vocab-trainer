from dataclasses import dataclass, replace
from datetime import datetime

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.shared.errors import EmptyTranslation, EmptyWord


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True, slots=True)
class Card:
    deck_id: int
    word: str
    translation: str
    fsrs: FsrsState
    transcription: str | None = None
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    @staticmethod
    def create(
        deck_id: int,
        word: str,
        translation: str,
        now: datetime,
        transcription: str | None = None,
        notes: str | None = None,
    ) -> "Card":
        clean_word = word.strip()
        if not clean_word:
            raise EmptyWord()
        clean_translation = translation.strip()
        if not clean_translation:
            raise EmptyTranslation()
        return Card(
            deck_id=deck_id,
            word=clean_word,
            translation=clean_translation,
            transcription=_clean_optional(transcription),
            notes=_clean_optional(notes),
            fsrs=FsrsState.new(now),
            created_at=now,
        )

    def with_fsrs(self, fsrs: FsrsState) -> "Card":
        return replace(self, fsrs=fsrs)
