from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.deck.deck import Deck
from vocab_api.infrastructure.persistence.tables import CardRow, DeckRow


def deck_to_row(deck: Deck) -> DeckRow:
    return DeckRow(id=deck.id, name=deck.name, created_at=deck.created_at)


def deck_from_row(row: DeckRow) -> Deck:
    return Deck(id=row.id, name=row.name, created_at=row.created_at)


def card_to_row(card: Card) -> CardRow:
    return CardRow(
        id=card.id,
        deck_id=card.deck_id,
        word=card.word,
        translation=card.translation,
        transcription=card.transcription,
        notes=card.notes,
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
        created_at=row.created_at,
        fsrs=FsrsState(
            due=row.fsrs_due,
            state=row.fsrs_state,
            step=row.fsrs_step,
            stability=row.fsrs_stability,
            difficulty=row.fsrs_difficulty,
            last_review=row.fsrs_last_review,
        ),
    )
