import httpx
import pytest

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.main import create_app


@pytest.fixture
async def client():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    app = create_app(container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await container.dispose()


async def test_progress_rolls_up_levels_and_streak(client: httpx.AsyncClient):
    deck = (await client.post("/decks", json={"name": "D"})).json()
    await client.post(
        f"/decks/{deck['id']}/import",
        json={"raw": "run,rʌn,бежать", "format": "csv", "dry_run": False},
    )
    queue = (await client.get("/review/queue", params={"deck_id": deck["id"], "limit": 5})).json()
    await client.post("/review", json={"card_id": queue[0]["id"], "rating": 3})
    mark = await client.post("/curriculum/lessons/b1.grammar.articles/read")
    assert mark.status_code == 200
    quiz = (await client.get("/curriculum/modules/b1.grammar.articles/quiz")).json()
    await client.post(
        "/curriculum/quiz/grade",
        json={
            "module_id": "b1.grammar.articles",
            "answers": [
                {"item_id": item["id"], "given": "0"} for item in quiz["items"]
            ],
        },
    )

    resp = await client.get("/progress")
    assert resp.status_code == 200
    body = resp.json()
    by_level = {level["level"]: level for level in body["levels"]}
    assert [level["level"] for level in body["levels"]] == [
        "A1", "A2", "B1", "B2", "C1", "C2",
    ]
    assert by_level["B1"]["completed"] == 1
    assert by_level["B1"]["total"] == 10
    assert by_level["A1"]["completed"] == 0
    assert body["streak"] == 1
    assert body["overall_percent"] > 0


async def test_module_detail_exposes_pillar_links(client: httpx.AsyncClient):
    phrasal = (await client.get("/curriculum/modules/b1.phrasal_verbs.work-business")).json()
    assert phrasal["vocab"] == ["main"]
    assert phrasal["interview_topic"] is None

    tech = (await client.get("/curriculum/modules/b2.vocabulary.technology")).json()
    assert tech["vocab"] == []
    assert tech["interview_topic"] == "Frontend"
