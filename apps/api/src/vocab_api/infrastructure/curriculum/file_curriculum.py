from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.domain.curriculum.lesson import Lesson
from vocab_api.domain.curriculum.map import CurriculumMap, LadderEntry
from vocab_api.domain.curriculum.module import Module
from vocab_api.domain.shared.errors import CurriculumModuleNotFound
from vocab_api.infrastructure.curriculum.content_loader import ContentBundle


class FileCurriculumRepository(CurriculumContent):
    """Curriculum content loaded from the bundled files at startup.

    The bundle is validated on load (fail fast on a broken curriculum) and then
    served read-only from memory — content is never written by the app.
    """

    def __init__(self, bundle: ContentBundle) -> None:
        self._bundle = bundle
        self._map: CurriculumMap[LadderEntry] = CurriculumMap(levels=bundle.levels())

    def map(self) -> CurriculumMap[LadderEntry]:
        return self._map

    def module(self, module_id: str) -> Module:
        module = self._bundle.module(module_id)
        if module is None:
            raise CurriculumModuleNotFound(module_id)
        return module

    def lesson(self, module_id: str) -> Lesson:
        lesson = self._bundle.lesson(module_id)
        if lesson is None:
            raise CurriculumModuleNotFound(module_id)
        return lesson

    def has_lesson(self, module_id: str) -> bool:
        return self._bundle.has_lesson(module_id)

    def has_quiz(self, module_id: str) -> bool:
        return self._bundle.has_quiz(module_id)

    def is_available(self, module_id: str) -> bool:
        # Phase 0 ships lessons without quizzes: a module is openable once its
        # lesson exists. Phase 1 tightens this to lesson AND quiz present.
        return self.has_lesson(module_id)