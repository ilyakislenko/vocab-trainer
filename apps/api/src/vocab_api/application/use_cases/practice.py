from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.application.ports.repositories import (
    CardRepository,
    SentenceAttemptRepository,
)
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.domain.shared.errors import EmptySentence


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
