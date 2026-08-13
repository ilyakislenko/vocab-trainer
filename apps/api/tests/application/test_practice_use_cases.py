import pytest
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeSentenceAttemptRepository,
    FixedClock,
    StubLlmProvider,
)

from vocab_api.application.use_cases.practice import CheckSentence, SuggestExample
from vocab_api.domain.card.card import Card
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.shared.errors import CardNotFound, EmptySentence


async def _card(cards: FakeCardRepository) -> int:
    (card,) = await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    assert card.id is not None
    return card.id


async def test_check_sentence_uses_card_word_and_persists():
    cards, attempts = FakeCardRepository(), FakeSentenceAttemptRepository()
    card_id = await _card(cards)
    llm = StubLlmProvider(
        Feedback(verdict=Verdict.NEEDS_WORK, feedback="Tense.", corrected="I ran.")
    )
    saved = await CheckSentence(cards, attempts, llm, FixedClock()).execute(card_id, "I runned.")
    assert saved.id is not None
    assert saved.feedback.corrected == "I ran."
    assert llm.checked == [("run", "I runned.")]
    assert await attempts.list_for_card(card_id) == [saved]


async def test_check_sentence_blank_raises():
    cards, attempts = FakeCardRepository(), FakeSentenceAttemptRepository()
    card_id = await _card(cards)
    with pytest.raises(EmptySentence):
        await CheckSentence(cards, attempts, StubLlmProvider(), FixedClock()).execute(card_id, "  ")


async def test_check_sentence_missing_card_raises():
    with pytest.raises(CardNotFound):
        await CheckSentence(
            FakeCardRepository(), FakeSentenceAttemptRepository(), StubLlmProvider(), FixedClock()
        ).execute(999, "hi")


async def test_suggest_example_returns_llm_text():
    cards = FakeCardRepository()
    card_id = await _card(cards)
    example = await SuggestExample(cards, StubLlmProvider(example="She runs.")).execute(card_id)
    assert example == "She runs."
