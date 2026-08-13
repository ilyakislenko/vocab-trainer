from typing import Literal

from pydantic import BaseModel

from vocab_api.domain.practice.feedback import Verdict


class CreateDeckIn(BaseModel):
    name: str


class DeckOut(BaseModel):
    id: int
    name: str


class ImportIn(BaseModel):
    raw: str
    format: Literal["csv", "markdown"]
    dry_run: bool = True


class CardOut(BaseModel):
    id: int | None
    word: str
    translation: str
    transcription: str | None


class RowErrorOut(BaseModel):
    line: int
    reason: str


class ImportOut(BaseModel):
    committed: bool
    imported: list[CardOut]
    errors: list[RowErrorOut]


class ReviewIn(BaseModel):
    card_id: int
    rating: Literal[1, 2, 3, 4]


class StatsOut(BaseModel):
    due_today: int
    total_reviews: int


class CheckSentenceIn(BaseModel):
    card_id: int
    sentence: str


class FeedbackOut(BaseModel):
    verdict: Verdict  # Pydantic serializes the StrEnum to "ok"/"needs_work"
    feedback: str
    corrected: str | None
    example: str | None


class ExampleOut(BaseModel):
    example: str
