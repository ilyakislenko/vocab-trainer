"""The daily Today session — the orchestrator (§10).

`BuildTodaySession` derives a deterministic ordered plan from current state on
each request (stateless, nothing is persisted): warm-up reviews, the
recommended learn step, one produce step, and the focus leeches. Completing
steps mutates the underlying state elsewhere, so re-fetching naturally
advances the plan.
"""

from datetime import datetime

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.curriculum_content import CurriculumContent
from vocab_api.application.ports.curriculum_repos import (
    ModuleProgressRepository,
    SkillItemRepository,
)
from vocab_api.application.ports.repositories import (
    CardRepository,
    DeckRepository,
    ReviewLogRepository,
)
from vocab_api.application.use_cases.curriculum import GetRecommendedModule
from vocab_api.application.use_cases.review import new_card_allowance
from vocab_api.domain.curriculum.progress import ModuleStatus
from vocab_api.domain.curriculum.today import (
    FocusStep,
    ProduceStep,
    ReadLessonStep,
    ReviewStep,
    TakeQuizStep,
    TodayStep,
)
from vocab_api.domain.shared.errors import CurriculumModuleNotFound


class BuildTodaySession:
    FOCUS_LIMIT = 3

    def __init__(
        self,
        content: CurriculumContent,
        progress: ModuleProgressRepository,
        decks: DeckRepository,
        cards: CardRepository,
        logs: ReviewLogRepository,
        skills: SkillItemRepository,
        recommend: GetRecommendedModule,
        clock: Clock,
    ) -> None:
        self._content = content
        self._progress = progress
        self._decks = decks
        self._cards = cards
        self._logs = logs
        self._skills = skills
        self._recommend = recommend
        self._clock = clock

    async def execute(self) -> tuple[TodayStep, ...]:
        now = self._clock.now()
        # Resolve the recommended module once — both the learn and produce steps
        # key off it, and it does not change within a single (read-only) request.
        recommended = await self._recommend.execute()
        steps: list[TodayStep] = []

        review = await self._review_step(now)
        if review is not None:
            steps.append(review)

        learn = await self._learn_step(recommended)
        if learn is not None:
            steps.append(learn)

        produce = await self._produce_step(recommended)
        if produce is not None:
            steps.append(produce)

        focus = await self._focus_step()
        if focus is not None:
            steps.append(focus)

        return tuple(steps)

    async def _review_step(self, now: datetime) -> ReviewStep | None:
        vocab_due = 0
        for deck in await self._decks.list():
            if deck.id is None:
                continue
            due = await self._cards.count_due(deck.id, now)
            new_count = await self._cards.count_new(deck.id)
            allowance = await new_card_allowance(self._cards, deck.id, now)
            vocab_due += due + min(allowance, new_count)
        skill_due = await self._skills.count_due(now)
        if vocab_due == 0 and skill_due == 0:
            return None
        return ReviewStep(vocab_due=vocab_due, skill_due=skill_due)

    async def _learn_step(
        self, module_id: str | None
    ) -> ReadLessonStep | TakeQuizStep | None:
        if module_id is None:
            return None
        try:
            module = self._content.module(module_id)
        except CurriculumModuleNotFound:
            return None
        progress = await self._progress.get(module_id)
        if progress.status is ModuleStatus.COMPLETED or not self._content.has_lesson(module_id):
            return None
        if progress.lesson_read_at is None:
            return ReadLessonStep(module_id=module.id, title=module.title)
        quiz = self._content.quiz(module_id)
        return TakeQuizStep(
            module_id=module.id,
            title=module.title,
            items=len(quiz.items),
        )

    async def _produce_step(self, module_id: str | None) -> ProduceStep | None:
        linked = self._produce_from_module(module_id)
        if linked is not None:
            return linked
        recent = await self._logs.most_recent(1)
        if not recent:
            return None
        card = await self._cards.get(recent[0])
        if card.id is None:
            return None
        return ProduceStep(word=card.word, card_id=card.id)

    def _produce_from_module(self, module_id: str | None) -> ProduceStep | None:
        """Prefer the recommended module's pillar links (§11/§5): vocab section
        before interview topic. Only links, never new vocab/interview code."""
        if module_id is None:
            return None
        try:
            module = self._content.module(module_id)
        except CurriculumModuleNotFound:
            return None
        if module.vocab:
            return ProduceStep(vocab_sections=module.vocab)
        if module.interview_topic:
            return ProduceStep(interview_topic=module.interview_topic)
        return None

    async def _focus_step(self) -> FocusStep | None:
        leeches = await self._skills.leeches(self.FOCUS_LIMIT)
        if not leeches:
            return None
        return FocusStep(leeches=tuple(leeches))