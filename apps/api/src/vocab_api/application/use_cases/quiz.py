"""Retrieval-practice use cases: serving a quiz and grading an attempt.

Only deterministic grading happens here (no LLM calls): each answer goes
through the pure `grade()` function. A graded miss on an `error_correction`
item with `llm_gradable` is flagged with `needs_llm` — the LLM path arrives
in Phase 2. Grading always records the attempt and, once the lesson is read,
completes the module (no score threshold).
"""

from dataclasses import dataclass

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import (
    ModuleProgressRepository,
    QuizAttemptRepository,
)
from vocab_api.application.use_cases.curriculum import GetRecommendedModule
from vocab_api.domain.curriculum.progress import ModuleProgress, ModuleStatus
from vocab_api.domain.curriculum.quiz import Quiz, grade
from vocab_api.domain.shared.errors import CurriculumQuizNotFound


@dataclass(frozen=True, slots=True)
class QuizItemResult:
    item_id: str
    skill: str
    correct: bool
    explanation: str
    needs_llm: bool = False


@dataclass(frozen=True, slots=True)
class QuizGradeOutcome:
    module_id: str
    items: tuple[QuizItemResult, ...]
    score: float
    status: ModuleStatus
    next_module_id: str | None


class GetModuleQuiz:
    """The quiz for a module; answers are stripped at the HTTP boundary."""

    def __init__(
        self, content: CurriculumContent, progress: ModuleProgressRepository
    ) -> None:
        self._content = content
        self._progress = progress

    async def execute(self, module_id: str) -> tuple[Quiz, ModuleProgress]:
        if not self._content.has_quiz(module_id) or not self._content.is_available(module_id):
            raise CurriculumQuizNotFound(module_id)
        quiz = self._content.quiz(module_id)
        progress = await self._progress.get(module_id)
        return quiz, progress


class GradeQuiz:
    def __init__(
        self,
        content: CurriculumContent,
        progress: ModuleProgressRepository,
        attempts: QuizAttemptRepository,
        clock: Clock,
    ) -> None:
        self._content = content
        self._progress = progress
        self._attempts = attempts
        self._clock = clock

    async def execute(
        self, module_id: str, answers: list[tuple[str, str]]
    ) -> QuizGradeOutcome:
        if not self._content.has_quiz(module_id) or not self._content.is_available(module_id):
            raise CurriculumQuizNotFound(module_id)
        quiz = self._content.quiz(module_id)

        now = self._clock.now()
        items_by_id = {item.id: item for item in quiz.items}
        results: list[QuizItemResult] = []
        for item_id, given in answers:
            item = items_by_id.get(item_id)
            if item is None:
                continue
            result = grade(item, given)
            await self._attempts.record(
                module_id=module_id,
                item_id=item_id,
                given=given,
                correct=result.correct,
                answered_at=now,
            )
            results.append(
                QuizItemResult(
                    item_id=item.id,
                    skill=item.skill,
                    correct=result.correct,
                    explanation=item.explanation,
                    needs_llm=result.needs_llm,
                )
            )

        graded = len(results)
        score = sum(1 for r in results if r.correct) / graded * 100.0 if graded else 0.0
        progress = await self._progress.mark_quiz_attempted(module_id, score, now)
        next_module = await GetRecommendedModule(self._content, self._progress).execute()
        return QuizGradeOutcome(
            module_id=module_id,
            items=tuple(results),
            score=score,
            status=progress.status,
            next_module_id=next_module,
        )
