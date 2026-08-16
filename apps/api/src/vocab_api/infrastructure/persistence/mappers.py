from datetime import UTC, datetime
from typing import overload

from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.infrastructure.persistence.tables import CardRow, DeckRow, SentenceAttemptRow


@overload
def _as_utc(dt: datetime) -> datetime: ...
@overload
def _as_utc(dt: None) -> None: ...
def _as_utc(dt: datetime | None) -> datetime | None:
    # SQLite drops tzinfo on round trip, so datetimes read back from the DB are
    # naive. The domain invariant is "always tz-aware UTC" (py-fsrs raises if fed a
    # mix of naive/aware datetimes), so re-attach UTC here at the mapper boundary.
    return dt.replace(tzinfo=UTC) if dt is not None and dt.tzinfo is None else dt


def deck_to_row(deck: Deck) -> DeckRow:
    return DeckRow(id=deck.id, name=deck.name, created_at=deck.created_at)


def deck_from_row(row: DeckRow) -> Deck:
    return Deck(id=row.id, name=row.name, created_at=_as_utc(row.created_at))


def card_to_row(card: Card) -> CardRow:
    return CardRow(
        id=card.id,
        deck_id=card.deck_id,
        word=card.word,
        translation=card.translation,
        transcription=card.transcription,
        notes=card.notes,
        section=card.section,
        created_at=card.created_at,
        fsrs_state=card.fsrs.state,
        fsrs_step=card.fsrs.step,
        fsrs_stability=card.fsrs.stability,
        fsrs_difficulty=card.fsrs.difficulty,
        fsrs_due=card.fsrs.due,
        fsrs_last_review=card.fsrs.last_review,
    )


def card_from_row(row: CardRow) -> Card:
    return Card(
        id=row.id,
        deck_id=row.deck_id,
        word=row.word,
        translation=row.translation,
        transcription=row.transcription,
        notes=row.notes,
        section=row.section,
        created_at=_as_utc(row.created_at),
        fsrs=FsrsState(
            due=_as_utc(row.fsrs_due),
            state=row.fsrs_state,
            step=row.fsrs_step,
            stability=row.fsrs_stability,
            difficulty=row.fsrs_difficulty,
            last_review=_as_utc(row.fsrs_last_review),
        ),
    )


def sentence_attempt_to_row(attempt: SentenceAttempt) -> SentenceAttemptRow:
    return SentenceAttemptRow(
        id=attempt.id,
        card_id=attempt.card_id,
        sentence=attempt.sentence,
        verdict=attempt.feedback.verdict.value,
        feedback=attempt.feedback.feedback,
        corrected=attempt.feedback.corrected,
        example=attempt.feedback.example,
        created_at=attempt.created_at,
    )


def sentence_attempt_from_row(row: SentenceAttemptRow) -> SentenceAttempt:
    return SentenceAttempt(
        id=row.id,
        card_id=row.card_id,
        sentence=row.sentence,
        feedback=Feedback(
            verdict=Verdict(row.verdict),
            feedback=row.feedback,
            corrected=row.corrected,
            example=row.example,
        ),
        created_at=_as_utc(row.created_at),
    )
