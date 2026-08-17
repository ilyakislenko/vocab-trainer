"""Placement diagnostic use cases (Phase 3).

`GetPlacement` serves the fixed diagnostic bank (no answers — the client
grades nothing). `GradePlacement` grades every answer with the same pure
`grade()` as quizzes, estimates the level, and persists it into the learner
profile together with the recommended-next module pointer.
"""

from dataclasses import dataclass

from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import LearnerProfileRepository
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import ModuleAvailability
from vocab_api.domain.curriculum.placement import Placement, estimate_level
from vocab_api.domain.curriculum.progress import LearnerProfile
from vocab_api.domain.curriculum.quiz import grade


@dataclass(frozen=True, slots=True)
class PlacementAnswer:
    item_id: str
    given: str


@dataclass(frozen=True, slots=True)
class PlacementResult:
    level: Level
    current_module_id: str | None


class GetPlacement:
    def __init__(self, content: CurriculumContent) -> None:
        self._content = content

    async def execute(self) -> Placement:
        return self._content.placement()


class GradePlacement:
    """Grade the diagnostic, persist the level, seed the starting module.

    Re-takeable: re-running only re-points the profile; existing
    `ModuleProgress` is never touched (§9).
    """

    def __init__(self, content: CurriculumContent, profile: LearnerProfileRepository) -> None:
        self._content = content
        self._profile = profile

    async def execute(self, answers: list[PlacementAnswer]) -> PlacementResult:
        placement = self._content.placement()
        by_id = {item.id: item for item in placement.items}
        results = tuple(
            grade(by_id[answer.item_id], answer.given)
            for answer in answers
            if answer.item_id in by_id
        )
        level = estimate_level(placement.items, results)
        current = self._first_available(level)
        await self._profile.save(LearnerProfile(placement_level=level, current_module_id=current))
        return PlacementResult(level=level, current_module_id=current)

    def _first_available(self, level: Level) -> str | None:
        authored = self._content.map()
        for section in authored.levels:
            if section.level is not level:
                continue
            for entry in section.entries:
                if entry.availability is ModuleAvailability.AVAILABLE:
                    return entry.id
        # Fallback: no authored module at that level yet — point at the first
        # available module anywhere so the learner always lands somewhere real.
        for section in authored.levels:
            for entry in section.entries:
                if entry.availability is ModuleAvailability.AVAILABLE:
                    return entry.id
        return None
