from typing import Protocol

from vocab_api.domain.curriculum.lesson import Lesson
from vocab_api.domain.curriculum.map import CurriculumMap, LadderEntry
from vocab_api.domain.curriculum.module import Module
from vocab_api.domain.curriculum.quiz import Quiz


class CurriculumContent(Protocol):
    """Read-only access to the authored curriculum bundle.

    Content lives in files (git-versioned) and is loaded into memory at
    startup; it is never written by the app. Each call returns immutable
    domain objects. Authoring (not-yet-published) modules are part of the map
    but have no lesson/quiz and cannot be opened.
    """

    def map(self) -> CurriculumMap[LadderEntry]: ...
    def module(self, module_id: str) -> Module: ...
    def lesson(self, module_id: str) -> Lesson: ...
    def quiz(self, module_id: str) -> Quiz: ...
    def has_lesson(self, module_id: str) -> bool: ...
    def has_quiz(self, module_id: str) -> bool: ...
    def is_available(self, module_id: str) -> bool: ...