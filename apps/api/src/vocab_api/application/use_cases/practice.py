from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.application.ports.question_bank import QuestionBank
from vocab_api.application.ports.repositories import (
    CardRepository,
    SentenceAttemptRepository,
)
from vocab_api.domain.card.card import Card
from vocab_api.domain.practice.interview import InterviewTurn
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.domain.practice.word_hint import WordHint
from vocab_api.domain.shared.errors import EmptySentence, EmptyTopic


class TranslateSentence:
    """Translate English text to Russian with in-memory cache."""

    _cache: dict[str, tuple[str, list[dict[str, str]]]]

    def __init__(self, llm: LlmProvider) -> None:
        self._llm = llm
        self._cache = {}

    async def execute(self, text: str) -> tuple[str, list[dict[str, str]]]:
        key = text.strip().lower()
        if key in self._cache:
            return self._cache[key]
        full, words = await self._llm.translate_sentence(text)
        if full or words:
            self._cache[key] = (full, words)
        return full, words


class CheckSentence:
    def __init__(
        self,
        cards: CardRepository,
        attempts: SentenceAttemptRepository,
        llm: LlmProvider,
        clock: Clock,
    ) -> None:
        self._cards = cards
        self._attempts = attempts
        self._llm = llm
        self._clock = clock

    async def execute(self, card_id: int, sentence: str) -> SentenceAttempt:
        card = await self._cards.get(card_id)  # raises CardNotFound
        if not sentence.strip():
            raise EmptySentence()
        feedback = await self._llm.check_sentence(card.word, sentence)
        attempt = SentenceAttempt.create(card_id, sentence, feedback, self._clock.now())
        return await self._attempts.add(attempt)


class SuggestExample:
    def __init__(self, cards: CardRepository, llm: LlmProvider) -> None:
        self._cards = cards
        self._llm = llm

    async def execute(self, card_id: int) -> str:
        card = await self._cards.get(card_id)  # raises CardNotFound
        return await self._llm.suggest_example(card.word)


class SelectTopicWords:
    def __init__(self, cards: CardRepository, llm: LlmProvider) -> None:
        self._cards = cards
        self._llm = llm

    async def execute(self, deck_id: int, topic: str, limit: int) -> list[Card]:
        words = await self._llm.select_topic_words(topic, limit)
        if not words:
            return []
        return await self._cards.by_words(deck_id, words)


class DescribeWord:
    def __init__(self, cards: CardRepository, llm: LlmProvider) -> None:
        self._cards = cards
        self._llm = llm

    async def execute(self, card_id: int) -> WordHint:
        card = await self._cards.get(card_id)  # raises CardNotFound
        return await self._llm.describe_word(card.word)


class DrillWord:
    def __init__(self, cards: CardRepository, llm: LlmProvider) -> None:
        self._cards = cards
        self._llm = llm

    async def execute(self, card_id: int, message: str) -> tuple[str, str]:
        card = await self._cards.get(card_id)  # raises CardNotFound
        return await self._llm.drill_word(card.word, message)


class ConductInterview:
    """Advance a job-interview chat.

    The opening question always comes from the bank. After that the LLM
    evaluates the candidate's last reply and decides how to continue: either a
    follow-up question in the interview language (question_id None, so the
    candidate keeps discussing without consuming a bank question) or an
    `advance` request, in which case the bank supplies the next question.
    Stateless: the caller sends the full message history on every turn.
    """

    def __init__(self, llm: LlmProvider, bank: QuestionBank) -> None:
        self._llm = llm
        self._bank = bank

    async def execute(
        self,
        topic: str,
        lang: str,
        used_question_ids: set[int],
        messages: list[dict[str, str]],
        mode: str = "auto",
    ) -> InterviewTurn:
        if not topic.strip():
            raise EmptyTopic()
        if mode == "next":
            question = self._bank.next(topic, used_question_ids)
            return InterviewTurn(
                verdict=None,
                feedback=None,
                corrected=None,
                question=question.ru if lang == "ru" else question.en,
                question_id=question.id,
            )
        if mode == "random":
            question = self._bank.random(topic, used_question_ids)
            return InterviewTurn(
                verdict=None,
                feedback=None,
                corrected=None,
                question=question.ru if lang == "ru" else question.en,
                question_id=question.id,
            )
        question = self._bank.next(topic, used_question_ids)
        text = question.ru if lang == "ru" else question.en
        if not messages:
            return InterviewTurn(
                verdict=None,
                feedback=None,
                corrected=None,
                question=text,
                question_id=question.id,
            )
        evaluation = await self._llm.interview(topic, lang, messages)
        if evaluation.advance or not evaluation.next_question:
            return InterviewTurn(
                verdict=evaluation.verdict,
                feedback=evaluation.feedback,
                corrected=evaluation.corrected,
                question=text,
                question_id=question.id,
            )
        return InterviewTurn(
            verdict=evaluation.verdict,
            feedback=evaluation.feedback,
            corrected=evaluation.corrected,
            question=evaluation.next_question,
            question_id=None,
        )
