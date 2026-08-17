from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import (
    LearnerProfileRepository,
    ModuleProgressRepository,
)
from vocab_api.domain.curriculum.lesson import Lesson
from vocab_api.domain.curriculum.map import (
    CurriculumMap,
    LevelOverview,
    ModuleOverview,
)
from vocab_api.domain.curriculum.module import Module
from vocab_api.domain.curriculum.progress import ModuleProgress, ModuleStatus
from vocab_api.domain.shared.errors import (
    CurriculumLessonNotFound,
    CurriculumModuleNotFound,
)


class GetCurriculumMap:
    """The full A1→C2 board, joining authored content with learner progress."""

    def __init__(
        self, content: CurriculumContent, progress: ModuleProgressRepository
    ) -> None:
        self._content = content
        self._progress = progress

    async def execute(self) -> CurriculumMap[ModuleOverview]:
        authored = self._content.map()
        rows = await self._progress.list()
        by_module = {row.module_id: row for row in rows}

        def status_of(module_id: str) -> ModuleProgress:
            return by_module.get(module_id, ModuleProgress(module_id=module_id))

        levels = tuple(
            LevelOverview(
                level=section.level,
                entries=tuple(
                    ModuleOverview.from_entry(
                        entry,
                        status_of(entry.id).status,
                        status_of(entry.id).quiz_best_score,
                        title=self._entry_title(entry.id, entry.title),
                    )
                    for entry in section.entries
                ),
            )
            for section in authored.levels
        )
        return CurriculumMap(levels=levels)

    def _entry_title(self, module_id: str, manifest_title: str) -> str:
        if manifest_title:
            return manifest_title
        module = self._content.module(module_id)
        return module.title if module is not None else ""


class GetModule:
    """Module detail for the learner (objectives, references, status)."""

    def __init__(
        self, content: CurriculumContent, progress: ModuleProgressRepository
    ) -> None:
        self._content = content
        self._progress = progress

    async def execute(self, module_id: str) -> tuple[Module, ModuleProgress]:
        module = self._safe_module(module_id)
        progress = await self._progress.get(module_id)
        return module, progress

    def has_quiz(self, module_id: str) -> bool:
        return self._content.has_quiz(module_id)

    def _safe_module(self, module_id: str) -> Module:
        module = self._content.module(module_id)  # raises CurriculumModuleNotFound
        if not self._content.is_available(module_id):
            raise CurriculumModuleNotFound(module_id)
        return module


class GetLesson:
    """The readable lesson for a module, for the reader screen."""

    def __init__(
        self, content: CurriculumContent, progress: ModuleProgressRepository
    ) -> None:
        self._content = content
        self._progress = progress

    async def execute(self, module_id: str) -> tuple[Lesson, ModuleProgress]:
        if not self._content.has_lesson(module_id) or not self._content.is_available(module_id):
            raise CurriculumLessonNotFound(module_id)
        lesson = self._content.lesson(module_id)
        progress = await self._progress.get(module_id)
        return lesson, progress


class MarkLessonRead:
    """Record that the learner read the lesson (idempotent)."""

    def __init__(
        self,
        content: CurriculumContent,
        progress: ModuleProgressRepository,
        clock: Clock,
    ) -> None:
        self._content = content
        self._progress = progress
        self._clock = clock

    async def execute(self, module_id: str) -> ModuleProgress:
        if not self._content.has_lesson(module_id) or not self._content.is_available(module_id):
            raise CurriculumLessonNotFound(module_id)
        return await self._progress.mark_lesson_read(module_id, self._clock.now())


class GetRecommendedModule:
    """The recommended next module: the placement pointer when still valid,
    otherwise the first not-completed available module in route order.

    The placement diagnostic (§9) seeds `current_module_id` — the learner's
    starting point. While that module is not completed (and still authored) it
    wins; once it is completed the recommendation resumes the route order.
    Used to surface a "next up" suggestion on the map and Today page. Pure
    recommendation — navigation stays free.
    """

    def __init__(
        self,
        content: CurriculumContent,
        progress: ModuleProgressRepository,
        profile: LearnerProfileRepository,
    ) -> None:
        self._content = content
        self._progress = progress
        self._profile = profile

    async def execute(self) -> str | None:
        authored = self._content.map()
        rows = await self._progress.list()
        completed = {row.module_id for row in rows if row.status is ModuleStatus.COMPLETED}

        pointer = (await self._profile.get()).current_module_id
        if pointer is not None and pointer not in completed and self._content.is_available(pointer):
            return pointer

        for section in authored.levels:
            for entry in section.entries:
                if entry.id in completed:
                    continue
                if self._content.is_available(entry.id):
                    return entry.id
        return None