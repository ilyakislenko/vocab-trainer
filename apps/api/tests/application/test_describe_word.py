from datetime import UTC, datetime

import pytest
from tests.conftest import FakeCardRepository, StubLlmProvider

from vocab_api.application.use_cases.practice import DescribeWord
from vocab_api.domain.card.card import Card
from vocab_api.domain.practice.word_hint import WordHint
from vocab_api.domain.shared.errors import CardNotFound

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


async def test_describes_word_from_card():
    cards = FakeCardRepository()
    await cards.add_many([Card.create(1, "run", "бежать", NOW)])
    hint = WordHint(meaning="Бежать.", example="I run every morning.")
    use_case = DescribeWord(cards, StubLlmProvider(hint=hint))
    assert await use_case.execute(1) == hint


async def test_raises_when_card_missing():
    cards = FakeCardRepository()
    use_case = DescribeWord(cards, StubLlmProvider())
    with pytest.raises(CardNotFound):
        await use_case.execute(999)
