"""A spaced-repetition unit for a micro-skill, reusing the FSRS machinery.

Mirrors the vocab `Card` aggregate: a frozen dataclass carrying the shared
`FsrsState`. `GradeQuiz` creates these for skills the learner gets wrong; the
`review-skills` flow advances them through the same `Scheduler`.
"""

from dataclasses import dataclass, replace
from datetime import datetime

from vocab_api.domain.card.fsrs_state import FsrsState

# A skill is a leech once it has failed this many review-state reviews
# (mirroring the FSRS convention; see spec §8.4).
LEECH_LAPSES = 4


@dataclass(frozen=True, slots=True)
class SkillItem:
    skill: str
    module_id: str
    source_item_id: str
    fsrs: FsrsState
    id: int | None = None

    @staticmethod
    def create(
        skill: str, module_id: str, source_item_id: str, now: datetime
    ) -> "SkillItem":
        return SkillItem(
            skill=skill,
            module_id=module_id,
            source_item_id=source_item_id,
            fsrs=FsrsState.new(now),
        )

    def with_fsrs(self, fsrs: FsrsState) -> "SkillItem":
        return replace(self, fsrs=fsrs)

    @property
    def is_leech(self) -> bool:
        return self.fsrs.lapses >= LEECH_LAPSES
