"""Pure quiz domain: item shapes and deterministic grading.

Grading is fully deterministic (no LLM here): each item type has its own
normalisation rule and the accepted-answer comparison is a pure function, so
every learner response produces a reproducible result. The optional LLM path
for `error_correction` lives in the use case, never in the domain.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

_SENTENCE_END = re.compile(r"[.?!\s]+$")
_WS = re.compile(r"\s+")


class QuizItemType(StrEnum):
    MCQ = "mcq"
    CLOZE = "cloze"
    TRANSFORM = "transform"
    ERROR_CORRECTION = "error_correction"
    WORD_ORDER = "word_order"
    LISTENING = "listening"


class GradableItem(Protocol):
    """Anything `grade()` can score (QuizItem, PlacementItem)."""

    @property
    def id(self) -> str: ...
    @property
    def skill(self) -> str: ...
    @property
    def type(self) -> QuizItemType: ...
    @property
    def options(self) -> tuple[str, ...] | None: ...
    @property
    def answer_index(self) -> int | None: ...
    @property
    def answers(self) -> tuple[str, ...] | None: ...
    @property
    def llm_gradable(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class QuizItem:
    id: str
    module_id: str
    type: QuizItemType
    skill: str
    prompt: str
    explanation: str
    options: tuple[str, ...] | None = None
    answer_index: int | None = None
    answers: tuple[str, ...] | None = None
    tokens: tuple[str, ...] | None = None
    llm_gradable: bool = False


@dataclass(frozen=True, slots=True)
class Quiz:
    module_id: str
    items: tuple[QuizItem, ...]


@dataclass(frozen=True, slots=True)
class GradeResult:
    item_id: str
    skill: str
    correct: bool
    needs_llm: bool = False


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def _cloze_value(text: str) -> str:
    """Cloze comparison: case-insensitive, trimmed."""
    return _fold(text).strip()


def _transform_value(text: str) -> str:
    """Transform/error-correction comparison: fold, collapse whitespace,
    strip sentence-ending punctuation."""
    value = _fold(text).strip()
    value = _WS.sub(" ", value)
    value = _SENTENCE_END.sub("", value)
    return value


def grade(item: GradableItem, given: str) -> GradeResult:
    """Grade one answer deterministically.

    `given` is always a string: for mcq it is the selected option index as a
    string ("0".."n-1"); for cloze/transform/error_correction it is the
    learner's free text. A single string type keeps the DTO mypy-strict clean
    (no str|int union).
    """
    if item.type is QuizItemType.MCQ:
        if item.answer_index is None:
            return GradeResult(item_id=item.id, skill=item.skill, correct=False)
        correct = given.strip() == str(item.answer_index)
        return GradeResult(item_id=item.id, skill=item.skill, correct=correct)

    accepted = item.answers or ()
    if item.type is QuizItemType.CLOZE:
        norm = _cloze_value(given)
        return GradeResult(
            item_id=item.id,
            skill=item.skill,
            correct=any(norm == _cloze_value(a) for a in accepted),
        )

    if item.type is QuizItemType.TRANSFORM:
        norm = _transform_value(given)
        return GradeResult(
            item_id=item.id,
            skill=item.skill,
            correct=any(norm == _transform_value(a) for a in accepted),
        )

    if item.type is QuizItemType.WORD_ORDER:
        # `given` is the learner's space-joined ordering; compare through the
        # same normalise-and-compare path so stray whitespace around tokens
        # does not decide the verdict.
        norm = _transform_value(given)
        return GradeResult(
            item_id=item.id,
            skill=item.skill,
            correct=any(norm == _transform_value(a) for a in accepted),
        )

    if item.type is QuizItemType.LISTENING:
        if item.options is not None:
            if item.answer_index is None:
                return GradeResult(item_id=item.id, skill=item.skill, correct=False)
            correct = given.strip() == str(item.answer_index)
            return GradeResult(item_id=item.id, skill=item.skill, correct=correct)
        # Dictation: type what you hear, cloze-style comparison.
        norm = _cloze_value(given)
        return GradeResult(
            item_id=item.id,
            skill=item.skill,
            correct=any(norm == _cloze_value(a) for a in accepted),
        )

    # error_correction
    norm = _transform_value(given)
    correct = any(norm == _transform_value(a) for a in accepted)
    return GradeResult(
        item_id=item.id,
        skill=item.skill,
        correct=correct,
        needs_llm=item.llm_gradable and not correct,
    )
