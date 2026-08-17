from datetime import UTC, datetime, timedelta

from vocab_api.application.ports.curriculum_repos import LearnerProfileRepository
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.curriculum.progress import LearnerProfile
from vocab_api.domain.curriculum.skill_item import SkillItem
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.interview import InterviewEvaluation, InterviewQuestion
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.domain.practice.word_hint import WordHint
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.domain.shared.errors import CardNotFound, DeckNotFound, SkillItemNotFound

FIXED_NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


class FixedClock:
    def __init__(self, now: datetime = FIXED_NOW) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class StubScheduler:
    """Deterministic scheduler: a rating advances due by rating days and lands
    the item in the Review state. Like the real py-fsrs adapter it does not own
    the lapse count (leaves it at the default), so use cases must carry lapses
    across a review themselves."""

    def review(self, state: FsrsState, rating: Rating, now: datetime) -> FsrsState:
        return FsrsState(
            due=now + timedelta(days=int(rating)),
            state=2,
            stability=1.0,
            last_review=now,
        )


class FakeDeckRepository:
    def __init__(self) -> None:
        self._items: dict[int, Deck] = {}
        self._seq = 0

    async def add(self, deck: Deck) -> Deck:
        self._seq += 1
        stored = Deck(id=self._seq, name=deck.name, created_at=deck.created_at)
        self._items[self._seq] = stored
        return stored

    async def get(self, deck_id: int) -> Deck:
        if deck_id not in self._items:
            raise DeckNotFound(deck_id)
        return self._items[deck_id]

    async def list(self) -> list[Deck]:
        return list(self._items.values())


class FakeCardRepository:
    def __init__(self) -> None:
        self._items: dict[int, Card] = {}
        self._seq = 0

    async def add_many(self, cards: list[Card]) -> list[Card]:
        saved: list[Card] = []
        for card in cards:
            self._seq += 1
            stored = Card(
                id=self._seq,
                deck_id=card.deck_id,
                word=card.word,
                translation=card.translation,
                fsrs=card.fsrs,
                transcription=card.transcription,
                notes=card.notes,
                section=card.section,
                created_at=card.created_at,
                introduced_at=card.introduced_at,
            )
            self._items[self._seq] = stored
            saved.append(stored)
        return saved

    async def get(self, card_id: int) -> Card:
        if card_id not in self._items:
            raise CardNotFound(card_id)
        return self._items[card_id]

    async def save(self, card: Card) -> None:
        assert card.id is not None
        self._items[card.id] = card

    async def due(self, deck_id: int, now: datetime) -> list[Card]:
        due = [
            c
            for c in self._items.values()
            if c.deck_id == deck_id and c.fsrs.state != 0 and c.fsrs.due <= now
        ]
        due.sort(key=lambda c: c.fsrs.due)
        return due

    async def new_cards(self, deck_id: int, limit: int) -> list[Card]:
        fresh = [c for c in self._items.values() if c.deck_id == deck_id and c.fsrs.state == 0]
        fresh.sort(key=lambda c: c.id or 0)
        return fresh[:limit]

    async def count_due(self, deck_id: int, now: datetime) -> int:
        return len(
            [
                c
                for c in self._items.values()
                if c.deck_id == deck_id and c.fsrs.state != 0 and c.fsrs.due <= now
            ]
        )

    async def count_new(self, deck_id: int) -> int:
        return len([c for c in self._items.values() if c.deck_id == deck_id and c.fsrs.state == 0])

    async def count_introduced_today(self, deck_id: int, start_of_day: datetime) -> int:
        return len(
            [
                c
                for c in self._items.values()
                if c.deck_id == deck_id
                and c.introduced_at is not None
                and c.introduced_at >= start_of_day
            ]
        )

    async def list_all(
        self, deck_id: int, limit: int, offset: int, section: str | None
    ) -> list[Card]:
        cards = [c for c in self._items.values() if c.deck_id == deck_id]
        if section is not None:
            cards = [c for c in cards if c.section == section]
        cards.sort(key=lambda c: c.id or 0)
        return cards[offset : offset + limit]

    async def by_words(self, deck_id: int, words: list[str]) -> list[Card]:
        lower = {w.lower() for w in words}
        return [c for c in self._items.values() if c.deck_id == deck_id and c.word.lower() in lower]

    async def count_by_state(self, deck_id: int) -> dict[str, int]:
        counts: dict[str, int] = {"new": 0, "learning": 0, "review": 0, "relearning": 0}
        for c in self._items.values():
            if c.deck_id == deck_id:
                state_map = {0: "new", 1: "learning", 2: "review", 3: "relearning"}
                name = state_map.get(c.fsrs.state, "unknown")
                counts[name] = counts.get(name, 0) + 1
        return counts

    async def soonest_due(self, deck_id: int, now: datetime) -> datetime | None:
        future = [
            c.fsrs.due
            for c in self._items.values()
            if c.deck_id == deck_id and c.fsrs.due > now
        ]
        return min(future) if future else None


class FakeReviewLogRepository:
    def __init__(self, cards: FakeCardRepository) -> None:
        # Mirrors the real repo's join against cards: card->deck is looked up live
        # off the shared card repository rather than snapshotted at add() time.
        self.entries: list[ReviewLogEntry] = []
        self._cards = cards

    async def add(self, entry: ReviewLogEntry) -> None:
        self.entries.append(entry)

    async def count_reviews(self, deck_id: int) -> int:
        count = 0
        for entry in self.entries:
            card = await self._cards.get(entry.card_id)
            if card.deck_id == deck_id:
                count += 1
        return count

    async def count_reviews_on(self, deck_id: int, day_start: datetime) -> int:
        count = 0
        for entry in self.entries:
            card = await self._cards.get(entry.card_id)
            if card.deck_id == deck_id and entry.reviewed_at >= day_start:
                count += 1
        return count

    async def streak(self, deck_id: int) -> int:
        # Simplified: count today if there are reviews, else 0.
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        for entry in self.entries:
            card = await self._cards.get(entry.card_id)
            if card.deck_id == deck_id and entry.reviewed_at.strftime("%Y-%m-%d") == today:
                return 1
        return 0

    async def activity(self, deck_id: int, days: int) -> list[dict[str, int | str]]:
        # Simplified: return today's count if any.
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        for entry in self.entries:
            card = await self._cards.get(entry.card_id)
            if card.deck_id == deck_id and entry.reviewed_at.strftime("%Y-%m-%d") == today:
                count += 1
        return [{"date": today, "count": count}] if count else []

    async def most_recent(self, limit: int) -> list[int]:
        newest = sorted(self.entries, key=lambda e: e.reviewed_at, reverse=True)
        return [entry.card_id for entry in newest[:limit]]


class FakeLearnerProfileRepository(LearnerProfileRepository):
    def __init__(self) -> None:
        self.profile = LearnerProfile()
        self.saves = 0

    async def get(self) -> LearnerProfile:
        return self.profile

    async def save(self, profile: LearnerProfile) -> None:
        self.profile = profile
        self.saves += 1


class FakeSkillItemRepository:
    def __init__(self) -> None:
        self._items: dict[int, SkillItem] = {}
        self._by_skill: dict[str, SkillItem] = {}
        self._seq = 0

    async def by_skill(self, skill: str) -> SkillItem | None:
        return self._by_skill.get(skill)

    async def get(self, skill_item_id: int) -> SkillItem:
        if skill_item_id not in self._items:
            raise SkillItemNotFound(skill_item_id)
        return self._items[skill_item_id]

    async def add(self, item: SkillItem) -> SkillItem:
        self._seq += 1
        stored = SkillItem(
            id=self._seq,
            skill=item.skill,
            module_id=item.module_id,
            source_item_id=item.source_item_id,
            fsrs=item.fsrs,
        )
        self._items[self._seq] = stored
        self._by_skill[stored.skill] = stored
        return stored

    async def save(self, item: SkillItem) -> None:
        assert item.id is not None
        self._items[item.id] = item
        self._by_skill[item.skill] = item

    async def due(self, now: datetime, limit: int) -> list[SkillItem]:
        due = [i for i in self._items.values() if i.fsrs.due <= now]
        due.sort(key=lambda i: i.fsrs.due)
        return due[:limit]

    async def count_due(self, now: datetime) -> int:
        return sum(1 for i in self._items.values() if i.fsrs.due <= now)

    async def leeches(self, limit: int) -> list[SkillItem]:
        leeches = [i for i in self._items.values() if i.is_leech]
        leeches.sort(key=lambda i: (-i.fsrs.lapses, i.fsrs.due))
        return leeches[:limit]


class FakeSentenceAttemptRepository:
    def __init__(self) -> None:
        self._items: list[SentenceAttempt] = []

    async def add(self, attempt: SentenceAttempt) -> SentenceAttempt:
        stored = SentenceAttempt(
            id=len(self._items) + 1,
            card_id=attempt.card_id,
            sentence=attempt.sentence,
            feedback=attempt.feedback,
            created_at=attempt.created_at,
        )
        self._items.append(stored)
        return stored

    async def list_for_card(self, card_id: int) -> list[SentenceAttempt]:
        return [a for a in self._items if a.card_id == card_id]


class StubLlmProvider:
    def __init__(
        self,
        feedback: Feedback | None = None,
        example: str = "An example.",
        topic_words: list[str] | None = None,
        hint: WordHint | None = None,
        interview_evaluation: InterviewEvaluation | None = None,
    ) -> None:
        self._feedback = feedback or Feedback(verdict=Verdict.OK, feedback="Good.")
        self._example = example
        self._topic_words = topic_words or []
        self._hint = hint or WordHint(meaning="A description.", example="An example.")
        self._interview_evaluation = interview_evaluation or InterviewEvaluation(
            verdict=None, feedback=None, corrected=None
        )
        self.checked: list[tuple[str, str]] = []

    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        self.checked.append((word, sentence))
        return self._feedback

    async def suggest_example(self, word: str) -> str:
        return self._example

    async def select_topic_words(self, topic: str, limit: int) -> list[str]:
        return self._topic_words[:limit]

    async def describe_word(self, word: str) -> WordHint:
        return self._hint

    async def drill_word(self, word: str, user_message: str) -> tuple[str, str]:
        return f"Nice use of '{word}'!", f"Can you use '{word}' in another sentence?"

    async def translate_sentence(self, text: str) -> tuple[str, list[dict[str, str]]]:
        return f"Перевод: {text}", []

    async def interview(
        self, topic: str, lang: str, difficulty: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        return self._interview_evaluation


class StubQuestionBank:
    def __init__(self, questions: list[InterviewQuestion] | None = None) -> None:
        self._questions = questions or [
            InterviewQuestion(
                id=1,
                topics=("Frontend", "React"),
                level="Middle",
                ru="Что такое props?",
                en="What are props?",
            ),
            InterviewQuestion(
                id=2,
                topics=("Frontend", "React"),
                level="Middle",
                ru="Что такое state?",
                en="What is state?",
            ),
        ]

    def next(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion:
        matching = [q for q in self._questions if topic in q.topics]
        if not matching:
            raise ValueError(f"No interview questions for topic {topic!r}")
        unused = [q for q in matching if q.id not in used_question_ids]
        return min(unused or matching, key=lambda q: q.id)

    def random(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion:
        matching = [q for q in self._questions if topic in q.topics]
        if not matching:
            raise ValueError(f"No interview questions for topic {topic!r}")
        unused = [q for q in matching if q.id not in used_question_ids]
        return (unused or matching)[0]
