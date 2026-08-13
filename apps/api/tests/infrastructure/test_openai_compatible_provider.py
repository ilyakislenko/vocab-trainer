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


async def test_check_sentence_raises_llm_unavailable_on_http_error_status():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_failing_client(500))
    with pytest.raises(LlmUnavailable):
        await provider.check_sentence("run", "I run.")


async def test_check_sentence_raises_llm_unavailable_on_connect_error():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_unreachable_client())
    with pytest.raises(LlmUnavailable):
        await provider.check_sentence("run", "I run.")
