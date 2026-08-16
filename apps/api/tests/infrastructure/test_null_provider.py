from vocab_api.domain.practice.feedback import Verdict
from vocab_api.infrastructure.llm.null_provider import NullProvider


async def test_null_provider_returns_disabled_feedback():
    provider = NullProvider()
    fb = await provider.check_sentence("run", "I run daily.")
    assert fb.verdict == Verdict.OK
    assert "disabled" in fb.feedback.lower()
    assert fb.corrected is None
    example = await provider.suggest_example("run")
    assert "run" in example


async def test_null_provider_returns_disabled_hint():
    provider = NullProvider()
    hint = await provider.describe_word("run")
    assert "disabled" in hint.meaning.lower()


async def test_null_provider_returns_disabled_interview_evaluation():
    provider = NullProvider()
    evaluation = await provider.interview("React", "en", [{"role": "user", "content": "hi"}])
    assert evaluation.verdict is None
    assert evaluation.feedback is None
    assert evaluation.corrected is None
    assert evaluation.advance is False
    assert evaluation.next_question is None
