from tests.conftest import FakeLearnerProfileRepository

from vocab_api.application.use_cases.placement import (
    GetPlacement,
    GradePlacement,
    PlacementAnswer,
)
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import (
    CurriculumMap,
    LadderEntry,
    LevelOverview,
    ModuleAvailability,
)
from vocab_api.domain.curriculum.placement import Placement, PlacementItem
from vocab_api.domain.curriculum.progress import LearnerProfile
from vocab_api.domain.curriculum.quiz import QuizItemType
from vocab_api.domain.curriculum.track import Track


def _item(item_id: str, level: Level) -> PlacementItem:
    return PlacementItem(
        id=item_id,
        level=level,
        skill="pl.probe",
        type=QuizItemType.MCQ,
        prompt="Pick the option",
        explanation="It is correct.",
        options=("right", "wrong"),
        answer_index=0,
    )


A2 = tuple(_item(f"a2.{i}", Level.A2) for i in range(6))
B1 = tuple(_item(f"b1.{i}", Level.B1) for i in range(6))
B2 = tuple(_item(f"b2.{i}", Level.B2) for i in range(6))
C1 = tuple(_item(f"c1.{i}", Level.C1) for i in range(6))
PLACEMENT = Placement(items=A2 + B1 + B2 + C1)

MAP = CurriculumMap(
    levels=(
        LevelOverview(
            level=Level.B1,
            entries=(
                LadderEntry(
                    id="b1.grammar.articles",
                    title="Articles",
                    track=Track.GRAMMAR,
                    availability=ModuleAvailability.AVAILABLE,
                ),
            ),
        ),
        LevelOverview(
            level=Level.C1,
            entries=(
                LadderEntry(
                    id="c1.grammar.cleft-sentences",
                    title="Cleft sentences",
                    track=Track.GRAMMAR,
                    availability=ModuleAvailability.AVAILABLE,
                ),
                LadderEntry(
                    id="c1.grammar.planned",
                    title="Planned",
                    track=Track.GRAMMAR,
                    availability=ModuleAvailability.AUTHORING,
                ),
            ),
        ),
        LevelOverview(
            level=Level.C2,
            entries=(
                LadderEntry(
                    id="c2.grammar.planned",
                    title="Planned",
                    track=Track.GRAMMAR,
                    availability=ModuleAvailability.AUTHORING,
                ),
            ),
        ),
    )
)


class FakeContent:
    def placement(self) -> Placement:
        return PLACEMENT

    def map(self) -> CurriculumMap[LadderEntry]:
        return MAP


async def test_get_placement_serves_the_bank():
    outcome = await GetPlacement(FakeContent()).execute()
    assert outcome.items == PLACEMENT.items
    assert len(outcome.items) >= 24


async def test_grade_placement_estimates_level_and_seeds_current_module():
    repo = FakeLearnerProfileRepository()
    answers = [PlacementAnswer(item_id=item.id, given="0") for item in A2 + B1 + B2 + C1]
    result = await GradePlacement(FakeContent(), repo).execute(answers)

    assert result.level is Level.C1
    assert result.current_module_id == "c1.grammar.cleft-sentences"
    assert repo.profile.placement_level is Level.C1
    assert repo.profile.current_module_id == "c1.grammar.cleft-sentences"


async def test_grade_placement_defaults_to_a1_and_falls_back_to_first_available():
    repo = FakeLearnerProfileRepository()
    # No authored C2 module -> fallback points at the first available anywhere.
    answers = [PlacementAnswer(item_id=item.id, given="9") for item in A2 + B1 + B2 + C1]
    result = await GradePlacement(FakeContent(), repo).execute(answers)

    assert result.level is Level.A1
    assert result.current_module_id == "b1.grammar.articles"


async def test_grade_placement_level_with_no_authored_module_falls_back():
    repo = FakeLearnerProfileRepository()
    answers = [PlacementAnswer(item_id=item.id, given="0") for item in A2]
    result = await GradePlacement(FakeContent(), repo).execute(answers)

    assert result.level is Level.A2
    # A2 has no available module in the fake map -> first available anywhere.
    assert result.current_module_id == "b1.grammar.articles"


async def test_grade_placement_ignores_unknown_item_ids():
    repo = FakeLearnerProfileRepository()
    answers = [
        PlacementAnswer(item_id="a2.0", given="0"),
        PlacementAnswer(item_id="ghost", given="0"),
    ]
    result = await GradePlacement(FakeContent(), repo).execute(answers)

    assert result.level is Level.A2
    assert repo.profile.placement_level is Level.A2


async def test_grade_placement_is_retakeable_and_preserves_progress():
    repo = FakeLearnerProfileRepository()
    await repo.save(LearnerProfile(placement_level=Level.B2, current_module_id="b1.x"))

    all_correct = [PlacementAnswer(item_id=item.id, given="0") for item in A2 + B1 + B2 + C1]
    result = await GradePlacement(FakeContent(), repo).execute(all_correct)

    assert result.level is Level.C1
    assert repo.profile.placement_level is Level.C1
    assert repo.profile.current_module_id == "c1.grammar.cleft-sentences"
