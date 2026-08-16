import httpx
import pytest

from vocab_api.application.errors import LlmUnavailable
from vocab_api.domain.practice.feedback import Verdict
from vocab_api.infrastructure.llm.openai_compatible_provider import OpenAiCompatibleProvider


def _client(content: str) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _failing_client(status_code: int) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "boom"})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _unreachable_client() -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_check_sentence_parses_json_feedback():
    content = (
        '{"verdict":"needs_work","feedback":"Wrong tense.",'
        '"corrected":"I ran.","example":"I run daily."}'
    )
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    fb = await provider.check_sentence("run", "I runned.")
    assert fb.verdict == Verdict.NEEDS_WORK
    assert fb.corrected == "I ran."
    assert fb.example == "I run daily."


async def test_check_sentence_tolerates_code_fences():
    content = '```json\n{"verdict":"ok","feedback":"Good."}\n```'
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    fb = await provider.check_sentence("run", "I run daily.")
    assert fb.verdict == Verdict.OK
    assert fb.corrected is None


async def test_check_sentence_falls_back_on_garbage():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("not json at all"))
    fb = await provider.check_sentence("run", "x")
    assert fb.verdict == Verdict.NEEDS_WORK
    assert "not json at all" in fb.feedback


async def test_suggest_example_returns_text():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("  She runs fast.  "))
    assert await provider.suggest_example("run") == "She runs fast."


async def test_select_topic_words_parses_json_array():
    provider = OpenAiCompatibleProvider(
        "http://x/v1", "m", client=_client('["run", "jump", "train"]')
    )
    assert await provider.select_topic_words("travel", 10) == ["run", "jump", "train"]


async def test_select_topic_words_respects_limit_and_ignores_non_strings():
    provider = OpenAiCompatibleProvider(
        "http://x/v1", "m", client=_client('["run", 5, null, "jump"]')
    )
    assert await provider.select_topic_words("travel", 1) == ["run"]


async def test_select_topic_words_falls_back_to_empty_on_garbage():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("no json"))
    assert await provider.select_topic_words("travel", 10) == []


async def test_describe_word_parses_json_hint():
    content = '{"meaning":"Бежать, двигаться быстро.","example":"I run every morning."}'
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    hint = await provider.describe_word("run")
    assert hint.meaning == "Бежать, двигаться быстро."
    assert hint.example == "I run every morning."


async def test_describe_word_falls_back_on_garbage():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("no json"))
    hint = await provider.describe_word("run")
    assert hint.example is None
    assert hint.meaning


async def test_check_sentence_raises_llm_unavailable_on_http_error_status():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_failing_client(500))
    with pytest.raises(LlmUnavailable):
        await provider.check_sentence("run", "I run.")


async def test_check_sentence_raises_llm_unavailable_on_connect_error():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_unreachable_client())
    with pytest.raises(LlmUnavailable):
        await provider.check_sentence("run", "I run.")


async def test_interview_parses_evaluation_when_no_answer_yet():
    content = '{"verdict":null,"feedback":null,"corrected":null}'
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    evaluation = await provider.interview("React", "en", "middle", [])
    assert evaluation.verdict is None
    assert evaluation.feedback is None
    assert evaluation.corrected is None
    assert evaluation.advance is False
    assert evaluation.next_question is None


async def test_interview_parses_feedback_and_corrected():
    content = (
        '{"verdict":"needs_work","feedback":"Отвечай полнее.",'
        '"corrected":"A component is a reusable piece of UI."}'
    )
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    evaluation = await provider.interview(
        "React",
        "en",
        "middle",
        [
            {"role": "interviewer", "content": "What is a component?"},
            {"role": "user", "content": "a thing"},
        ],
    )
    assert evaluation.verdict == Verdict.NEEDS_WORK
    assert evaluation.feedback == "Отвечай полнее."
    assert evaluation.corrected == "A component is a reusable piece of UI."


async def test_interview_parses_followup_and_advance():
    content = (
        '{"verdict":"ok","feedback":"Хорошо.",'
        '"corrected":null,"advance":true,"next_question":null}'
    )
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    evaluation = await provider.interview(
        "React",
        "en",
        "middle",
        [
            {"role": "interviewer", "content": "What are props?"},
            {"role": "user", "content": "next"},
        ],
    )
    assert evaluation.verdict == Verdict.OK
    assert evaluation.advance is True
    assert evaluation.next_question is None


async def test_interview_parses_followup_when_not_advancing():
    content = (
        '{"verdict":"ok","feedback":"Хорошо.",'
        '"corrected":null,"advance":false,"next_question":"Can you elaborate?"}'
    )
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    evaluation = await provider.interview(
        "React", "en", "middle", [{"role": "user", "content": "a thing"}]
    )
    assert evaluation.advance is False
    assert evaluation.next_question == "Can you elaborate?"


async def test_interview_parses_explanation_when_verdict_null():
    content = (
        '{"verdict":null,"feedback":"Props это свойства компонента.",'
        '"corrected":null,"advance":false,"next_question":"What are props used for?"}'
    )
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    evaluation = await provider.interview(
        "React", "en", "middle", [{"role": "user", "content": "объясни"}]
    )
    assert evaluation.verdict is None
    assert evaluation.feedback == "Props это свойства компонента."
    assert evaluation.advance is False
    assert evaluation.next_question == "What are props used for?"


async def test_interview_falls_back_on_garbage():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("not json"))
    evaluation = await provider.interview("React", "en", "middle", [])
    assert evaluation.verdict is None
    assert evaluation.feedback == "not json"
    assert evaluation.advance is False
    assert evaluation.next_question is None
