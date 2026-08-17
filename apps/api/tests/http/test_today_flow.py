import httpx
import pytest
from tests.http._placement_bank import correct_answers, fetch_diagnostic

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


async def _seed_deck(client: httpx.AsyncClient, words: str) -> int:
    deck = (await client.post("/decks", json={"name": "Travel"})).json()
    committed = await client.post(
        f"/decks/{deck['id']}/import",
        json={"raw": words, "format": "csv", "dry_run": False},
    )
    assert committed.json()["committed"] is True
    return deck["id"]


async def test_today_plans_review_and_read_lesson(client: httpx.AsyncClient):
    await _seed_deck(client, "run,rʌn,бежать\njump,dʒʌmp,прыгать")

    resp = await client.get("/session/today")
    assert resp.status_code == 200
    steps = resp.json()["steps"]

    assert [step["kind"] for step in steps] == ["review", "read_lesson"]
    assert steps[0]["vocab_due"] == 2
    assert steps[0]["skill_due"] == 0
    assert steps[1]["module_id"] == "a1.grammar.to-be"
    assert steps[1]["level"] == "A1"
    assert steps[1]["track"] == "grammar"


async def test_today_include_produce_after_first_review(client: httpx.AsyncClient):
    await _seed_deck(client, "run,rʌn,бежать")
    queue = (await client.get("/review/queue", params={"deck_id": 1, "limit": 10})).json()
    card_id = queue[0]["id"]
    word = queue[0]["word"]

    await client.post("/review", json={"card_id": card_id, "rating": 3})

    steps = (await client.get("/session/today")).json()["steps"]
    produce = next(s for s in steps if s["kind"] == "produce")
    assert produce["word"] == word
    assert produce["card_id"] == card_id
    assert produce["vocab_sections"] == []
    assert produce["interview_topic"] is None


async def test_today_switches_to_take_quiz_after_lesson_read(client: httpx.AsyncClient):
    await _seed_deck(client, "run,rʌn,бежать")
    mark = await client.post("/curriculum/lessons/a1.grammar.to-be/read")
    assert mark.status_code == 200

    steps = (await client.get("/session/today")).json()["steps"]
    kinds = [step["kind"] for step in steps]
    assert "read_lesson" not in kinds
    quiz = next(s for s in steps if s["kind"] == "take_quiz")
    assert quiz["module_id"] == "a1.grammar.to-be"
    assert quiz["items"] >= 1
    assert steps[0]["kind"] == "review"
    assert steps[0]["vocab_due"] == 1


async def test_today_reflects_placement_pointer(client: httpx.AsyncClient):
    items = await fetch_diagnostic(client)
    grade = await client.post("/placement/grade", json={"answers": correct_answers(items)})
    assert grade.status_code == 200
    assert grade.json()["level"] == "C1"

    steps = (await client.get("/session/today")).json()["steps"]
    learn = next(s for s in steps if s["kind"] in {"read_lesson", "take_quiz"})
    assert learn["module_id"] == "c1.grammar.cleft-sentences"
