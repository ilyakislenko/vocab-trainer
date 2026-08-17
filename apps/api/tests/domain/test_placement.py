import random

from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.placement import (
    DIAGNOSTIC_PER_LEVEL,
    Placement,
    PlacementItem,
    estimate_level,
    sample_diagnostic,
)
from vocab_api.domain.curriculum.quiz import GradeResult, QuizItemType


def _item(item_id: str, level: Level) -> PlacementItem:
    return PlacementItem(
        id=item_id,
        level=level,
        skill="pl.probe",
        type=QuizItemType.MCQ,
        prompt="?",
        explanation="?",
        options=("x", "y"),
        answer_index=0,
    )


A2_ITEMS = tuple(_item(f"a2.{i}", Level.A2) for i in range(6))
B1_ITEMS = tuple(_item(f"b1.{i}", Level.B1) for i in range(6))
B2_ITEMS = tuple(_item(f"b2.{i}", Level.B2) for i in range(6))
C1_ITEMS = tuple(_item(f"c1.{i}", Level.C1) for i in range(6))
ITEMS = A2_ITEMS + B1_ITEMS + B2_ITEMS + C1_ITEMS


def _ok(item_id: str) -> GradeResult:
    return GradeResult(item_id=item_id, skill="pl.probe", correct=True)


def _miss(item_id: str) -> GradeResult:
    return GradeResult(item_id=item_id, skill="pl.probe", correct=False)


def test_all_correct_estimates_c1():
    results = tuple(_ok(item.id) for item in ITEMS)
    assert estimate_level(ITEMS, results) is Level.C1


def test_none_pass_defaults_to_a1():
    results = tuple(_miss(item.id) for item in ITEMS)
    assert estimate_level(ITEMS, results) is Level.A1


def test_highest_passing_level_with_all_lower_passing():
    # A2, B1, B2 pass, C1 misses -> B2 (the highest with every lower band passing).
    results = tuple(_ok(item.id) for item in A2_ITEMS + B1_ITEMS + B2_ITEMS) + tuple(
        _miss(item.id) for item in C1_ITEMS
    )
    assert estimate_level(ITEMS, results) is Level.B2


def test_monotonic_rule_blocks_a_lucky_top_level():
    # C1 passes perfectly but B2 fails -> the estimate cannot skip B2.
    results = (
        tuple(_ok(item.id) for item in A2_ITEMS + B1_ITEMS)
        + tuple(_miss(item.id) for item in B2_ITEMS)
        + tuple(_ok(item.id) for item in C1_ITEMS)
    )
    assert estimate_level(ITEMS, results) is Level.B1


def test_unanswered_levels_do_not_pass():
    # Only C1 items are answered (all correct): no lower-band evidence, so the
    # monotonic rule cannot place above A1.
    results = tuple(_ok(item.id) for item in C1_ITEMS)
    assert estimate_level(ITEMS, results) is Level.A1


def test_threshold_is_at_least_seventy_percent():
    # A2 passes, B1 hits 5/6 (0.83) -> B1; B1 at 4/6 (0.67) -> A2.
    passing = (
        tuple(_ok(item.id) for item in A2_ITEMS)
        + tuple(_ok(item.id) for item in B1_ITEMS[:5])
        + tuple(_miss(item.id) for item in B1_ITEMS[5:])
    )
    assert estimate_level(ITEMS, passing) is Level.B1

    failing = (
        tuple(_ok(item.id) for item in A2_ITEMS)
        + tuple(_ok(item.id) for item in B1_ITEMS[:4])
        + tuple(_miss(item.id) for item in B1_ITEMS[4:])
    )
    assert estimate_level(ITEMS, failing) is Level.A2


def test_empty_results_default_to_a1():
    assert estimate_level(ITEMS, ()) is Level.A1


def test_sample_diagnostic_is_seed_reproducible():
    rng = random.Random(42)
    first = sample_diagnostic(ITEMS, rng)
    second = sample_diagnostic(ITEMS, random.Random(42))
    assert first.items == second.items


def test_sample_diagnostic_picks_per_level_from_each_tested_level():
    outcome = sample_diagnostic(ITEMS, random.Random(7))
    by_level: dict[Level, int] = {}
    for item in outcome.items:
        by_level[item.level] = by_level.get(item.level, 0) + 1
    assert len(outcome.items) == DIAGNOSTIC_PER_LEVEL * 4
    assert by_level == {
        Level.A2: DIAGNOSTIC_PER_LEVEL,
        Level.B1: DIAGNOSTIC_PER_LEVEL,
        Level.B2: DIAGNOSTIC_PER_LEVEL,
        Level.C1: DIAGNOSTIC_PER_LEVEL,
    }


def test_sample_diagnostic_variates_across_seeds():
    big_bank = ITEMS + tuple(
        _item(f"x.{level.value}.{i}", level)
        for level in (Level.A2, Level.B1, Level.B2, Level.C1)
        for i in range(4)
    )
    outcome = sample_diagnostic(big_bank, random.Random(1))
    other = sample_diagnostic(big_bank, random.Random(2))
    assert outcome.items != other.items


def test_sample_diagnostic_returns_placement_in_deterministic_order():
    outcome = sample_diagnostic(ITEMS, random.Random(3))
    assert isinstance(outcome, Placement)
    order = {lv: i for i, lv in enumerate((Level.A2, Level.B1, Level.B2, Level.C1))}
    levels = [item.level for item in outcome.items]
    assert levels == sorted(levels, key=order.__getitem__)
