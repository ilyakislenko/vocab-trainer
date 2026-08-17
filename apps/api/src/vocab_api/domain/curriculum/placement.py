"""Placement diagnostic: item shapes, sampling, and the level estimate.

The content bundle is a large bank of items spanning A2→C1. Each attempt
samples a fixed-size diagnostic from the bank (selection randomizes, grading
stays deterministic). Items are graded with the same pure `grade()` as
quizzes (they satisfy the `GradableItem` protocol).
"""

import random
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

# A level counts as passed when at least this share of its answered items are
# correct. The named constant drives the level estimate (and is tested).
PLACEMENT_PASS_RATE = 0.7

# How many items from each tested level make up one diagnostic attempt.
DIAGNOSTIC_PER_LEVEL = 6

# The content bundle must hold at least this many items per tested level so a
# diagnostic can be freshly sampled each attempt (Spec D1).
PLACEMENT_ITEMS_PER_LEVEL_MIN = 12


def sample_diagnostic(
    items: tuple[PlacementItem, ...],
    rng: random.Random,
    per_level: int = DIAGNOSTIC_PER_LEVEL,
) -> Placement:
    """Sample a fixed-size diagnostic: ``per_level`` items from each level.

    Only the selection randomizes; grading stays deterministic. The sampled
    items are returned in the deterministic serving order (A2→C1, then by id)
    so the UI is stable.
    """
    by_level: dict[Level, list[PlacementItem]] = {}
    for item in items:
        by_level.setdefault(item.level, []).append(item)

    sampled: list[PlacementItem] = []
    for level in TESTED_LEVELS:
        pool = by_level.get(level, [])
        chosen = rng.sample(pool, min(per_level, len(pool)))
        sampled.extend(chosen)

    order = {level: index for index, level in enumerate(TESTED_LEVELS)}
    sampled.sort(key=lambda i: (order[i.level], i.id))
    return Placement(items=tuple(sampled))


def correct_answer(item: PlacementItem) -> str:
    """The canonical correct answer for an item, for post-test review."""
    if item.answers:
        return item.answers[0]
    if item.options and item.answer_index is not None:
        return item.options[item.answer_index]
    return ""


def given_answer(item: PlacementItem, given: str) -> str:
    """The learner's answer as display text for the post-test review.

    For mcq, ``given`` is the selected option index as a string; resolve it to
    the option text so the review shows readable words, not a bare index (it is
    then symmetric with ``correct_answer``). Cloze/transform answers are already
    text and pass through; an unanswered or malformed value passes through too.
    """
    if item.type is QuizItemType.MCQ and item.options is not None:
        try:
            index = int(given)
        except ValueError:
            return given
        if 0 <= index < len(item.options):
            return item.options[index]
    return given


def estimate_level(items: tuple[PlacementItem, ...], results: tuple[GradeResult, ...]) -> Level:
    """Highest level such that that level and every lower tested level each pass.

    Monotonic rule (Spec D4): a level passes when at least
    ``PLACEMENT_PASS_RATE`` of its *answered* items are correct; a level with
    no answered items does not pass (there is no evidence for it). The result
    is the highest level with all tested levels from A2 up to it passing, and
    ``A1`` when even A2 does not pass. This prevents a single lucky answer at
    a high level from placing a learner above clearly failed lower bands.
    """
    correct_by_level: dict[Level, list[bool]] = {}
    outcome_by_id = {r.item_id: r for r in results}
    for item in items:
        outcome = outcome_by_id.get(item.id)
        if outcome is not None:
            correct_by_level.setdefault(item.level, []).append(outcome.correct)

    estimated = Level.A1
    for level in TESTED_LEVELS:
        correct = correct_by_level.get(level, [])
        if not correct:
            break
        if sum(correct) / len(correct) < PLACEMENT_PASS_RATE:
            break
        estimated = level
    return estimated
