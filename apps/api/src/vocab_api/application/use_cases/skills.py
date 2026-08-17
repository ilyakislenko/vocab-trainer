"""Spaced-repetition use cases for skill items (Phase 2).

Wrong quiz answers surface here on an FSRS schedule: the queue serves due
skills enriched with their source quiz item (so the review UI can show the
prompt and reveal the answer), rating runs the same `Scheduler` as vocab
review and tracks lapses, and leech detection pinpoints weak spots.
"""

from dataclasses import dataclass, replace

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import SkillItemRepository
from vocab_api.application.ports.scheduler import Scheduler
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.curriculum.quiz import QuizItem, QuizItemType
from vocab_api.domain.curriculum.skill_item import SkillItem


@dataclass(frozen=True, slots=True)
class SkillReviewItem:
    """A due skill item enriched with its source quiz item for display."""

    id: int
    skill: str
    module_id: str
    source_item_id: str
    is_leech: bool
    type: QuizItemType
    prompt: str
    options: tuple[str, ...] | None
    answers: tuple[str, ...]
    explanation: str


class GetSkillReviewQueue:
    def __init__(
        self, skills: SkillItemRepository, content: CurriculumContent, clock: Clock
    ) -> None:
        self._skills = skills
        self._content = content
        self._clock = clock

    async def execute(self, limit: int) -> list[SkillReviewItem]:
        due = await self._skills.due(self._clock.now(), limit)
        enriched: list[SkillReviewItem] = []
        # Cache source items per module: several due skills usually share one module.
        sources: dict[str, dict[str, QuizItem]] = {}
        for item in due:
            by_id = sources.get(item.module_id)
            if by_id is None:
                by_id = {qi.id: qi for qi in self._content.quiz(item.module_id).items}
                sources[item.module_id] = by_id
            source = by_id.get(item.source_item_id)
            if source is None:
                # A stale source item means the content changed; never surface
                # a review the learner cannot self-check.
                continue
            enriched.append(self._enrich(item, source))
        return enriched

    def _enrich(
        self, item: SkillItem, source: QuizItem
    ) -> SkillReviewItem:
        answers: tuple[str, ...]
        if source.type is QuizItemType.MCQ and source.answer_index is not None:
            answers = (source.options[source.answer_index],) if source.options else ()
        else:
            answers = tuple(source.answers) if source.answers is not None else ()
        return SkillReviewItem(
            id=item.id or 0,
            skill=item.skill,
            module_id=item.module_id,
            source_item_id=item.source_item_id,
            is_leech=item.is_leech,
            type=source.type,
            prompt=source.prompt,
            options=source.options,
            answers=answers,
            explanation=source.explanation,
        )


class RecordSkillReview:
    def __init__(
        self, skills: SkillItemRepository, scheduler: Scheduler, clock: Clock
    ) -> None:
        self._skills = skills
        self._scheduler = scheduler
        self._clock = clock

    async def execute(self, skill_item_id: int, rating: Rating) -> SkillItem:
        now = self._clock.now()
        item = await self._skills.get(skill_item_id)  # raises SkillItemNotFound
        fsrs = self._scheduler.review(item.fsrs, rating, now)
        # A lapse is Again on an item that has already graduated past initial
        # learning — Review (2) or Relearning (3). Counting relearning relapses
        # too lets a skill you keep bombing reach the Focus list within a
        # session, so weak-spot help surfaces promptly instead of only after
        # several spaced-out cycles. First-time learning misses (state 0/1)
        # don't count — everyone fumbles something new once.
        lapses = item.fsrs.lapses
        if rating is Rating.AGAIN and item.fsrs.state in (2, 3):
            lapses += 1
        updated = item.with_fsrs(replace(fsrs, lapses=lapses))
        await self._skills.save(updated)
        return updated


class GetFocusLeeches:
    """Top-N leeches — the learner's weak spots, weakest first (§8.4)."""

    def __init__(self, skills: SkillItemRepository) -> None:
        self._skills = skills

    async def execute(self, limit: int) -> list[SkillItem]:
        return await self._skills.leeches(limit)
