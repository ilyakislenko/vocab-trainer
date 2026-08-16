from datetime import UTC, datetime

from tests.conftest import FakeCardRepository, StubLlmProvider

from vocab_api.application.use_cases.practice import SelectTopicWords
from vocab_api.domain.card.card import Card

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


async def _cards() -> FakeCardRepository:
    cards = FakeCardRepository()
    await cards.add_many(
        [
            Card.create(1, "run", "бежать", NOW),
            Card.create(1, "jump", "прыгать", NOW),
            Card.create(1, "train", "поезд", NOW),
        ]
    )
    return cards


async def test_returns_cards_matching_llm_words_case_insensitively():
    cards = await _cards()
    use_case = SelectTopicWords(cards, StubLlmProvider(topic_words=["Run", "Train", "absent"]))
    result = await use_case.execute(1, "travel", 10)
    assert {c.word for c in result} == {"run", "train"}


async def test_returns_nothing_when_llm_produces_no_words():
    cards = await _cards()
    use_case = SelectTopicWords(cards, StubLlmProvider(topic_words=[]))
    assert await use_case.execute(1, "travel", 10) == []


async def test_respects_limit():
    cards = await _cards()
    use_case = SelectTopicWords(cards, StubLlmProvider(topic_words=["run", "jump", "train"]))
    result = await use_case.execute(1, "travel", 2)
    assert len(result) == 2
