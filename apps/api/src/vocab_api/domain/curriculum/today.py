"""Today session steps: the typed, ordered plan for the day (§10).

A session is a deterministic list of steps. Each step is a small discriminated
union carrying exactly the ids/payload the front-end needs to render it and
deep-link to the existing screen that performs the work. The session is never
persisted — it is derived from current state on every request.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from vocab_api.domain.curriculum.skill_item import SkillItem


class TodayStepKind(StrEnum):
    REVIEW = "review"
    READ_LESSON = "read_lesson"
    TAKE_QUIZ = "take_quiz"
    PRODUCE = "produce"
    FOCUS = "focus"


@dataclass(frozen=True, slots=True)
class ReviewStep:
    """Warm-up: due vocab cards and due skill items (interleaved, §10.1)."""

    kind: Literal[TodayStepKind.REVIEW] = TodayStepKind.REVIEW
    vocab_due: int = 0
    skill_due: int = 0


@dataclass(frozen=True, slots=True)
class ReadLessonStep:
    """Learn: the recommended module still has an unread lesson."""

    module_id: str
    title: str
    kind: Literal[TodayStepKind.READ_LESSON] = TodayStepKind.READ_LESSON


@dataclass(frozen=True, slots=True)
class TakeQuizStep:
    """Learn: the recommended module's lesson is read, quiz is next."""

    module_id: str
    title: str
    items: int
    kind: Literal[TodayStepKind.TAKE_QUIZ] = TodayStepKind.TAKE_QUIZ


@dataclass(frozen=True, slots=True)
class ProduceStep:
    """Output task: a sentence prompt on the most recently reviewed word."""

    word: str
    card_id: int
    kind: Literal[TodayStepKind.PRODUCE] = TodayStepKind.PRODUCE


@dataclass(frozen=True, slots=True)
class FocusStep:
    """Weak spots: up to three leeches to drill (§8.4)."""

    kind: Literal[TodayStepKind.FOCUS] = TodayStepKind.FOCUS
    leeches: tuple[SkillItem, ...] = ()


TodayStep = (
    ReviewStep
    | ReadLessonStep
    | TakeQuizStep
    | ProduceStep
    | FocusStep
)

# Deterministic presentation order of a session (§10).
STEP_ORDER: tuple[TodayStepKind, ...] = (
    TodayStepKind.REVIEW,
    TodayStepKind.READ_LESSON,
    TodayStepKind.TAKE_QUIZ,
    TodayStepKind.PRODUCE,
    TodayStepKind.FOCUS,
)