from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar

from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.progress import ModuleStatus
from vocab_api.domain.curriculum.track import Track


class ModuleAvailability(StrEnum):
    """Whether authored content exists for the module.

    Every module appears in the ladder (visible from day one); `AUTHORING`
    marks a module whose lesson/quiz files have not landed yet — shown as
    "being added", not openable.
    """

    AVAILABLE = "available"
    AUTHORING = "authoring"


@dataclass(frozen=True, slots=True)
class LadderEntry:
    """One row of the curriculum ladder as authored in the manifest.

    Carries just enough for the map: the stable id, a display title, its track
    and whether content is available. Learner state is joined by the use case.
    """

    id: str
    title: str
    track: Track
    availability: ModuleAvailability


EntryT = TypeVar("EntryT")


@dataclass(frozen=True, slots=True)
class LevelOverview[EntryT]:
    """A CEFR level on the map with its ordered module rows."""

    level: Level
    entries: tuple[EntryT, ...]


@dataclass(frozen=True, slots=True)
class ModuleOverview:
    """A module row as the learner sees it: content availability + progress."""

    id: str
    title: str
    track: Track
    availability: ModuleAvailability
    status: ModuleStatus
    quiz_best_score: float | None = None

    @staticmethod
    def from_entry(
        entry: LadderEntry, progress: ModuleStatus, score: float | None, title: str | None = None
    ) -> "ModuleOverview":
        return ModuleOverview(
            id=entry.id,
            title=title or entry.title,
            track=entry.track,
            availability=entry.availability,
            status=progress,
            quiz_best_score=score,
        )


@dataclass(frozen=True, slots=True)
class CurriculumMap[EntryT]:
    """The full A1→C2 board: ordered levels, each with ordered module rows.

    Generic over the row type so the authored map (LadderEntry) and the
    learner-facing map (ModuleOverview) share one shape without losing types.
    """

    levels: tuple[LevelOverview[EntryT], ...]