"""Placement diagnostic: item shapes and the deterministic level estimate.

The diagnostic is a fixed-length set of items spanning A2→C1 in a
deterministic order. Items are graded with the same pure `grade()` as quizzes
(they satisfy the `GradableItem` protocol), and the resulting level is the
highest tested level at which the learner answered at least 70% correctly.
"""

from dataclasses import dataclass

from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.quiz import GradeResult, QuizItemType


@dataclass(frozen=True, slots=True)
class PlacementItem:
    id: str
    level: Level
    skill: str
    type: QuizItemType
    prompt: str
    explanation: str
    options: tuple[str, ...] | None = None
    answer_index: int | None = None
    answers: tuple[str, ...] | None = None
    llm_gradable: bool = False


@dataclass(frozen=True, slots=True)
class Placement:
    items: tuple[PlacementItem, ...]


# The levels actually tested by the diagnostic (A1 and C2 are not — A1 is the
# fallback result, C2 requires the top of the C1 band plus full course work).
TESTED_LEVELS: tuple[Level, ...] = (Level.A2, Level.B1, Level.B2, Level.C1)

# A level counts as passed when at least this share of its items are correct.
PLACEMENT_PASS_RATE = 0.7


def estimate_level(items: tuple[PlacementItem, ...], results: tuple[GradeResult, ...]) -> Level:
    """Highest level with >= 70% correct; A1 when none passes.

    `results` may omit items the learner did not answer; an unanswered item is
    simply not counted, so the per-level ratio is over answered items only.
    """
    correct_by_level: dict[Level, list[bool]] = {}
    result_by_id = {r.item_id: r for r in results}
    for item in items:
        result = result_by_id.get(item.id)
        if result is not None:
            correct_by_level.setdefault(item.level, []).append(result.correct)

    for level in reversed(TESTED_LEVELS):
        correct = correct_by_level.get(level, [])
        if not correct:
            continue
        if sum(correct) / len(correct) >= PLACEMENT_PASS_RATE:
            return level
    return Level.A1
