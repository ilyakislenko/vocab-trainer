from datetime import datetime

from sqlmodel import Field, SQLModel


class DeckRow(SQLModel, table=True):
    __tablename__ = "decks"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime | None = None


class CardRow(SQLModel, table=True):
    __tablename__ = "cards"
    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(index=True, foreign_key="decks.id")
    word: str
    translation: str
    transcription: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    fsrs_state: int = 1
    fsrs_step: int | None = 0
    fsrs_stability: float | None = None
    fsrs_difficulty: float | None = None
    fsrs_due: datetime = Field(index=True)
    fsrs_last_review: datetime | None = None


class ReviewLogRow(SQLModel, table=True):
    __tablename__ = "review_logs"
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(index=True, foreign_key="cards.id")
    rating: int
    reviewed_at: datetime
