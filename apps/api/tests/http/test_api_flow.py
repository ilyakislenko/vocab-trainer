import httpx
import pytest

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.main import create_app


@pytest.fixture
async def client():
    container = Container(
        Settings(database_url="sqlite+aiosqlite:///:memory:", llm_provider="none")
    )
    await container.init()
    app = create_app(container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_full_flow_create_import_review_stats(client: httpx.AsyncClient):
    deck = (await client.post("/decks", json={"name": "Travel"})).json()
    deck_id = deck["id"]

    preview = await client.post(
        f"/decks/{deck_id}/import",
        json={"raw": "run,rʌn,бежать", "format": "csv", "dry_run": True},
    )
    assert preview.json()["committed"] is False

    committed = await client.post(
        f"/decks/{deck_id}/import",
        json={"raw": "run,rʌn,бежать\njump,dʒʌmp,прыгать", "format": "csv", "dry_run": False},
    )
    assert committed.json()["committed"] is True
    assert len(committed.json()["imported"]) == 2

    queue = (await client.get("/review/queue", params={"deck_id": deck_id, "limit": 10})).json()
    assert len(queue) == 2
    first_id = queue[0]["id"]

    reviewed = await client.post("/review", json={"card_id": first_id, "rating": 3})
    assert reviewed.status_code == 200

    stats = (await client.get("/stats", params={"deck_id": deck_id})).json()
    assert stats["total_reviews"] == 1
    assert stats["due_today"] == 1  # one card reviewed and pushed out, one still due


async def test_import_into_missing_deck_returns_404(client: httpx.AsyncClient):
    resp = await client.post(
        "/decks/999/import", json={"raw": "run,бежать", "format": "csv", "dry_run": True}
    )
    assert resp.status_code == 404
