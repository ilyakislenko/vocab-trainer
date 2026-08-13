import httpx
import pytest

from vocab_api.application.errors import LlmUnavailable
from vocab_api.application.use_cases.practice import CheckSentence
from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.domain.practice.feedback import Feedback
from vocab_api.main import create_app


class RaisingLlm:
    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        raise LlmUnavailable("The language model is unavailable.")

    async def suggest_example(self, word: str) -> str:
        raise LlmUnavailable("The language model is unavailable.")


@pytest.fixture
async def client():
    # llm_provider defaults to "none"
    container = Container(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    await container.init()
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_check_and_example_with_null_provider(client: httpx.AsyncClient):
    deck = (await client.post("/decks", json={"name": "T"})).json()
    await client.post(
        f"/decks/{deck['id']}/import",
        json={"raw": "run,бежать", "format": "csv", "dry_run": False},
    )
    queue = await client.get("/review/queue", params={"deck_id": deck["id"], "limit": 5})
    card = queue.json()[0]

    checked = await client.post(
        "/practice/check", json={"card_id": card["id"], "sentence": "I run."}
    )
    assert checked.status_code == 200
    body = checked.json()
    assert body["verdict"] == "ok"
    assert "disabled" in body["feedback"].lower()

    example = await client.get("/practice/example", params={"card_id": card["id"]})
    assert example.status_code == 200
    assert "run" in example.json()["example"]


async def test_check_missing_card_404(client: httpx.AsyncClient):
    resp = await client.post("/practice/check", json={"card_id": 999, "sentence": "hi"})
    assert resp.status_code == 404


async def test_check_returns_502_when_llm_provider_unavailable():
    # llm_provider defaults to "none"; swap the check_sentence use case's llm
    # for one that raises LlmUnavailable, reusing the container's own repos/clock.
    container = Container(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    await container.init()
    original = container.check_sentence
    container.check_sentence = CheckSentence(
        original._cards, original._attempts, RaisingLlm(), original._clock
    )
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        deck = (await client.post("/decks", json={"name": "T"})).json()
        await client.post(
            f"/decks/{deck['id']}/import",
            json={"raw": "run,бежать", "format": "csv", "dry_run": False},
        )
        queue = await client.get("/review/queue", params={"deck_id": deck["id"], "limit": 5})
        card = queue.json()[0]

        resp = await client.post(
            "/practice/check", json={"card_id": card["id"], "sentence": "I run."}
        )
    assert resp.status_code == 502
    assert resp.json() == {"detail": "The language model is unavailable."}
