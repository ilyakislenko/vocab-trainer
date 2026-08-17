from datetime import UTC, datetime

from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.progress import LearnerProfile, ModuleProgress, ModuleStatus


def test_level_order_is_ascending_a1_to_c2():
    ordered = [Level.A1, Level.A2, Level.B1, Level.B2, Level.C1, Level.C2]
    assert [lvl.order() for lvl in ordered] == [0, 1, 2, 3, 4, 5]


def test_module_progress_defaults_to_not_started():
    progress = ModuleProgress(module_id="b1.grammar.articles")
    assert progress.status is ModuleStatus.NOT_STARTED
    assert progress.lesson_read_at is None
    assert progress.quiz_best_score is None
    assert progress.completed_at is None


def test_derive_status_moves_not_started_to_in_progress_on_lesson_read():
    read_at = datetime(2026, 8, 16, 9, 0, tzinfo=UTC)
    progress = ModuleProgress(module_id="b1.grammar.articles")
    derived = progress.derive_status(lesson_read_at=read_at, quiz_attempted=False, now=read_at)
    assert derived.status is ModuleStatus.IN_PROGRESS
    assert derived.lesson_read_at == read_at
    assert derived.completed_at is None


def test_derive_status_completes_when_lesson_read_and_quiz_attempted():
    read_at = datetime(2026, 8, 16, 9, 0, tzinfo=UTC)
    progress = ModuleProgress(module_id="b1.grammar.articles")
    derived = progress.derive_status(lesson_read_at=read_at, quiz_attempted=True, now=read_at)
    assert derived.status is ModuleStatus.COMPLETED
    assert derived.completed_at == read_at


def test_derive_status_keeps_not_started_when_nothing_happened():
    now = datetime(2026, 8, 16, 9, 0, tzinfo=UTC)
    progress = ModuleProgress(module_id="b1.grammar.articles")
    derived = progress.derive_status(lesson_read_at=None, quiz_attempted=False, now=now)
    assert derived.status is ModuleStatus.NOT_STARTED
    assert derived.lesson_read_at is None


def test_learner_profile_has_optional_placement_and_current_module():
    profile = LearnerProfile()
    assert profile.placement_level is None
    assert profile.current_module_id is None
    advanced = LearnerProfile(placement_level=Level.B1, current_module_id="b1.grammar.articles")
    assert advanced.placement_level is Level.B1
    assert advanced.current_module_id == "b1.grammar.articles"
