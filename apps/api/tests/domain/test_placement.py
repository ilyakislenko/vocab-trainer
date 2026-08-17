from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.placement import PlacementItem, estimate_level
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
C1_ITEMS = tuple(_item(f"c1.{i}", Level.C1) for i in range(6))
ITEMS = A2_ITEMS + B1_ITEMS + C1_ITEMS


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


def test_highest_passing_level_wins():
    # C1 misses, B1 and A2 pass -> B1 (the highest passing).
    results = tuple(_ok(item.id) for item in A2_ITEMS + B1_ITEMS) + tuple(
        _miss(item.id) for item in C1_ITEMS
    )
    assert estimate_level(ITEMS, results) is Level.B1


def test_threshold_is_at_least_seventy_percent():
    # 5/6 (0.83) passes, 4/6 (0.67) fails.
    passing = tuple(_ok(item.id) for item in B1_ITEMS[:5]) + tuple(
        _miss(item.id) for item in B1_ITEMS[5:]
    )
    assert estimate_level(ITEMS, passing) is Level.B1

    failing = tuple(_ok(item.id) for item in B1_ITEMS[:4]) + tuple(
        _miss(item.id) for item in B1_ITEMS[4:]
    )
    assert estimate_level(ITEMS, failing) is Level.A1


def test_unanswered_items_are_not_counted():
    # Only one C1 item answered and it is correct: 100% of answered items,
    # so C1 passes.
    results = (_ok(C1_ITEMS[0].id),)
    assert estimate_level(ITEMS, results) is Level.C1


def test_empty_results_default_to_a1():
    assert estimate_level(ITEMS, ()) is Level.A1
