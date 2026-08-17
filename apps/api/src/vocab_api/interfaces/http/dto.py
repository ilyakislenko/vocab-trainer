from datetime import datetime
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
    section: str | None = None


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
    streak: int = 0
    fsrs_new: int = 0
    fsrs_learning: int = 0
    fsrs_review: int = 0
    fsrs_relearning: int = 0
    activity: list[dict[str, int | str]] = []


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


class WordHintOut(BaseModel):
    meaning: str
    example: str | None = None


class DrillIn(BaseModel):
    card_id: int
    message: str


class DrillOut(BaseModel):
    response: str
    question: str | None = None


class WordTranslation(BaseModel):
    word: str
    translation: str


class SentenceTranslation(BaseModel):
    full: str
    words: list[WordTranslation] = []


class InterviewMessage(BaseModel):
    role: Literal["user", "interviewer"]
    content: str


class InterviewIn(BaseModel):
    topic: str
    lang: Literal["ru", "en"] = "en"
    difficulty: Literal["junior", "middle", "senior"] = "middle"
    mode: Literal["auto", "next", "random"] = "auto"
    used_question_ids: list[int] = []
    messages: list[InterviewMessage] = []


class InterviewOut(BaseModel):
    verdict: Verdict | None = None
    feedback: str | None = None
    corrected: str | None = None
    question: str
    question_id: int | None = None


class CurriculumModuleOut(BaseModel):
    id: str
    title: str
    level: str
    track: str
    availability: str
    status: str
    quiz_best_score: float | None = None


class CurriculumLevelOut(BaseModel):
    level: str
    modules: list[CurriculumModuleOut]


class CurriculumMapOut(BaseModel):
    levels: list[CurriculumLevelOut]
    recommended_module_id: str | None = None


class CurriculumReferenceOut(BaseModel):
    book: str
    locator: str


class CurriculumModuleDetailOut(BaseModel):
    id: str
    title: str
    level: str
    track: str
    status: str
    objectives: list[str]
    references: list[CurriculumReferenceOut]
    has_quiz: bool
    estimated_minutes: int
    quiz_best_score: float | None = None


class CurriculumLessonMetaOut(BaseModel):
    id: str
    title: str
    level: str
    track: str
    estimated_minutes: int
    objectives: list[str]
    skills: list[str]
    references: list[CurriculumReferenceOut]


class CurriculumLessonOut(BaseModel):
    markdown: str
    meta: CurriculumLessonMetaOut


class CurriculumModuleProgressOut(BaseModel):
    module_id: str
    status: str
    lesson_read_at: datetime | None = None
    quiz_best_score: float | None = None
    completed_at: datetime | None = None


class CurriculumQuizItemOut(BaseModel):
    """A quiz item as served to the learner — answers are never sent."""

    id: str
    type: str
    skill: str
    prompt: str
    options: list[str] | None = None


class CurriculumQuizOut(BaseModel):
    module_id: str
    status: str
    items: list[CurriculumQuizItemOut]


class CurriculumQuizAnswerIn(BaseModel):
    item_id: str
    given: str


class CurriculumQuizGradeIn(BaseModel):
    module_id: str
    answers: list[CurriculumQuizAnswerIn]


class CurriculumQuizItemResultOut(BaseModel):
    item_id: str
    skill: str
    correct: bool
    explanation: str
    needs_llm: bool = False


class CurriculumQuizGradeOut(BaseModel):
    module_id: str
    score: float
    status: str
    completed: bool
    next_module_id: str | None = None
    items: list[CurriculumQuizItemResultOut]
