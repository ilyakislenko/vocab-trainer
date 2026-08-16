import pytest
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeSentenceAttemptRepository,
    FixedClock,
    StubLlmProvider,
    StubQuestionBank,
)

from vocab_api.application.use_cases.practice import CheckSentence, ConductInterview, SuggestExample
from vocab_api.domain.card.card import Card
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.interview import InterviewEvaluation
from vocab_api.domain.shared.errors import CardNotFound, EmptySentence, EmptyTopic


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


async def test_conduct_interview_asks_opening_question_from_bank():
    bank = StubQuestionBank()
    result = await ConductInterview(StubLlmProvider(), bank).execute(
        "React",
        "en",
        set(),
        [],
    )
    assert result.question == "What are props?"
    assert result.question_id == 1
    assert result.verdict is None
    assert result.feedback is None


async def test_conduct_interview_localizes_question_to_ru():
    bank = StubQuestionBank()
    result = await ConductInterview(StubLlmProvider(), bank).execute("React", "ru", set(), [])
    assert result.question == "Что такое props?"
    assert result.question_id == 1


async def test_conduct_interview_never_repeats_used_question():
    bank = StubQuestionBank()
    use_case = ConductInterview(StubLlmProvider(), bank)
    first = await use_case.execute("React", "en", set(), [])
    second = await use_case.execute("React", "en", {first.question_id}, [])
    assert second.question_id != first.question_id
    assert second.question == "What is state?"


async def test_conduct_interview_delegates_evaluation_to_llm():
    evaluation = InterviewEvaluation(
        verdict=Verdict.OK, feedback="Хорошо.", corrected="Better answer."
    )
    llm = StubLlmProvider(interview_evaluation=evaluation)
    result = await ConductInterview(llm, StubQuestionBank()).execute(
        "React",
        "en",
        {1},
        [
            {"role": "interviewer", "content": "What are props?"},
            {"role": "user", "content": "A reusable piece of UI."},
        ],
    )
    assert result.verdict == Verdict.OK
    assert result.feedback == "Хорошо."
    assert result.corrected == "Better answer."
    assert result.question == "What is state?"
    assert result.question_id == 2


async def test_conduct_interview_blank_topic_raises():
    with pytest.raises(EmptyTopic):
        await ConductInterview(StubLlmProvider(), StubQuestionBank()).execute(
            "   ", "en", set(), []
        )


async def test_conduct_interview_uses_llm_followup_when_not_advancing():
    evaluation = InterviewEvaluation(
        verdict=Verdict.OK,
        feedback="Хорошо.",
        corrected=None,
        advance=False,
        next_question="Can you elaborate?",
    )
    llm = StubLlmProvider(interview_evaluation=evaluation)
    result = await ConductInterview(llm, StubQuestionBank()).execute(
        "React",
        "en",
        {1},
        [
            {"role": "interviewer", "content": "What are props?"},
            {"role": "user", "content": "A reusable piece of UI."},
        ],
    )
    assert result.verdict == Verdict.OK
    assert result.question == "Can you elaborate?"
    assert result.question_id is None


async def test_conduct_interview_advances_to_bank_when_llm_requests():
    evaluation = InterviewEvaluation(
        verdict=Verdict.OK,
        feedback="Хорошо.",
        corrected=None,
        advance=True,
        next_question=None,
    )
    llm = StubLlmProvider(interview_evaluation=evaluation)
    result = await ConductInterview(llm, StubQuestionBank()).execute(
        "React",
        "en",
        {1},
        [
            {"role": "interviewer", "content": "What are props?"},
            {"role": "user", "content": "next"},
        ],
    )
    assert result.question == "What is state?"
    assert result.question_id == 2


async def test_conduct_interview_mode_next_skips_llm():
    result = await ConductInterview(StubLlmProvider(), StubQuestionBank()).execute(
        "React", "en", {1}, [], mode="next"
    )
    assert result.question == "What is state?"
    assert result.question_id == 2
    assert result.verdict is None


async def test_conduct_interview_mode_random_skips_llm():
    result = await ConductInterview(StubLlmProvider(), StubQuestionBank()).execute(
        "React", "en", set(), [], mode="random"
    )
    assert result.question_id in {1, 2}
    assert result.verdict is None
