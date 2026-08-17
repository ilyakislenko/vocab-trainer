"""A1→C2 progress roll-up for the dashboard (§12 `/progress`).

Pure read model over the curriculum map + module progress + review activity:
per-level completion counts against the full authored ladder (authoring stubs
included — the manifest is the whole path), the overall percent, and the
current review streak (reused from the existing per-deck stats, taking the
strongest deck).
"""

from dataclasses import dataclass

from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import ModuleProgressRepository
from vocab_api.application.ports.repositories import (
    DeckRepository,
    ReviewLogRepository,
)
from vocab_api.domain.curriculum.level import Level
from vocab_api.domain.curriculum.progress import ModuleStatus


@dataclass(frozen=True, slots=True)
class LevelProgress:
    level: Level
    completed: int
    total: int


@dataclass(frozen=True, slots=True)
class ProgressReport:
    levels: tuple[LevelProgress, ...]
    overall_percent: int
    streak: int


class GetProgress:
    def __init__(
        self,
        content: CurriculumContent,
        progress: ModuleProgressRepository,
        decks: DeckRepository,
        logs: ReviewLogRepository,
    ) -> None:
        self._content = content
        self._progress = progress
        self._decks = decks
        self._logs = logs

    async def execute(self) -> ProgressReport:
        authored = self._content.map()
        rows = await self._progress.list()
        completed_ids = {
            row.module_id for row in rows if row.status is ModuleStatus.COMPLETED
        }

        levels: list[LevelProgress] = []
        for section in authored.levels:
            ids = {entry.id for entry in section.entries}
            levels.append(
                LevelProgress(
                    level=section.level,
                    completed=len(ids & completed_ids),
                    total=len(ids),
                )
            )

        total = sum(level.total for level in levels)
        done = sum(level.completed for level in levels)
        overall = round(100 * done / total) if total else 0

        streak = 0
        for deck in await self._decks.list():
            if deck.id is None:
                continue
            streak = max(streak, await self._logs.streak(deck.id))

        return ProgressReport(levels=tuple(levels), overall_percent=overall, streak=streak)