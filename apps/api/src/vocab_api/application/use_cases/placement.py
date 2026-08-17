"""Placement diagnostic use cases.

`GetPlacement` samples a fixed-size diagnostic from the bank (no answers — the
client grades nothing). `GradePlacement` grades every answer with the same
pure `grade()` as quizzes, estimates the level monotonically, persists it into
the learner profile together with the recommended-next module pointer, and
returns per-item results for the post-test review.
"""

import random
from dataclasses import dataclass

from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import LearnerProfileRepository
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.map import ModuleAvailability
from vocab_api.domain.curriculum.placement import (
    Placement,
    correct_answer,
    estimate_level,
    sample_diagnostic,
)
from vocab_api.domain.curriculum.progress import LearnerProfile
from vocab_api.domain.curriculum.quiz import grade


@dataclass(frozen=True, slots=True)
class PlacementAnswer:
    item_id: str
    given: str


@dataclass(frozen=True, slots=True)
class PlacementItemResult:
    """One graded item for the post-test review (Spec D3)."""

    item_id: str
    level: Level
    skill: str
    prompt: str
    given: str
    correct: bool
    correct_answer: str
    explanation: str


@dataclass(frozen=True, slots=True)
class PlacementResult:
    level: Level
    current_module_id: str | None
    results: tuple[PlacementItemResult, ...]


class GetPlacement:
    def __init__(self, content: CurriculumContent, rng: random.Random) -> None:
        self._content = content
        self._rng = rng

    async def execute(self) -> Placement:
        bank = self._content.placement().items
        return sample_diagnostic(bank, self._rng)


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
        grade_results = []
        item_results: list[PlacementItemResult] = []
        for answer in answers:
            item = by_id.get(answer.item_id)
            if item is None:
                continue
            outcome = grade(item, answer.given)
            grade_results.append(outcome)
            item_results.append(
                PlacementItemResult(
                    item_id=item.id,
                    level=item.level,
                    skill=item.skill,
                    prompt=item.prompt,
                    given=answer.given,
                    correct=outcome.correct,
                    correct_answer=correct_answer(item),
                    explanation=item.explanation,
                )
            )
        level = estimate_level(placement.items, tuple(grade_results))
        current = self._first_available(level)
        await self._profile.save(LearnerProfile(placement_level=level, current_module_id=current))
        return PlacementResult(level=level, current_module_id=current, results=tuple(item_results))

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
