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


ALL_CORRECT = {
    "pl.a2.1": "1",
    "pl.a2.2": "2",
    "pl.a2.3": "0",
    "pl.a2.4": "is going to",
    "pl.a2.5": "2",
    "pl.a2.6": "0",
    "pl.b1.1": "0",
    "pl.b1.2": "2",
    "pl.b1.3": "1",
    "pl.b1.4": "was",
    "pl.b1.5": "1",
    "pl.b1.6": "1",
    "pl.b2.1": "0",
    "pl.b2.2": "1",
    "pl.b2.3": "whose",
    "pl.b2.4": "1",
    "pl.b2.5": "2",
    "pl.b2.6": "0",
    "pl.c1.1": "0",
    "pl.c1.2": "Seen",
    "pl.c1.3": "1",
    "pl.c1.4": "1",
    "pl.c1.5": "No sooner",
    "pl.c1.6": "0",
}


def _answers(ids: list[str]) -> list[dict[str, str]]:
    return [{"item_id": item_id, "given": ALL_CORRECT[item_id]} for item_id in ids]


async def test_placement_returns_items_without_answers(client: httpx.AsyncClient):
    resp = await client.get("/placement")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 24
    by_level: dict[str, int] = {}
    for item in items:
        assert item["id"]
        assert item["skill"]
        assert item["prompt"]
        assert item["level"] in {"A2", "B1", "B2", "C1"}
        assert "answer_index" not in item
        assert "answers" not in item
        assert "explanation" not in item
        if item["type"] == "mcq":
            assert item["options"]
        else:
            assert item["options"] is None
        by_level[item["level"]] = by_level.get(item["level"], 0) + 1
    assert len(by_level) == 4
    assert all(count >= 6 for count in by_level.values())


async def test_grade_placement_all_correct_gives_c1(client: httpx.AsyncClient):
    resp = await client.post("/placement/grade", json={"answers": _answers(list(ALL_CORRECT))})
    assert resp.status_code == 200
    result = resp.json()
    assert result["level"] == "C1"
    assert result["current_module_id"] == "c1.grammar.cleft-sentences"

    map_resp = await client.get("/curriculum")
    assert map_resp.json()["placement_level"] == "C1"


async def test_grade_placement_defaults_to_a1(client: httpx.AsyncClient):
    wrong = [{"item_id": item_id, "given": "bogus"} for item_id in ALL_CORRECT]
    resp = await client.post("/placement/grade", json={"answers": wrong})
    assert resp.status_code == 200
    result = resp.json()
    assert result["level"] == "A1"
    # A1/A2 have no authored modules yet -> the first available anywhere.
    assert result["current_module_id"] == "b1.grammar.articles"


async def test_grade_placement_returns_highest_passing_level(client: httpx.AsyncClient):
    passing = [item_id for item_id in ALL_CORRECT if item_id.startswith(("pl.a2.", "pl.b1."))]
    wrong = [
        {"item_id": item_id, "given": "bogus"} for item_id in ALL_CORRECT if item_id not in passing
    ]
    resp = await client.post(
        "/placement/grade",
        json={"answers": _answers(passing) + wrong},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["level"] == "B1"
    assert result["current_module_id"] == "b1.grammar.articles"


async def test_grade_placement_is_retakeable(client: httpx.AsyncClient):
    first = await client.post("/placement/grade", json={"answers": _answers(list(ALL_CORRECT))})
    assert first.json()["level"] == "C1"

    wrong = [{"item_id": item_id, "given": "bogus"} for item_id in ALL_CORRECT]
    second = await client.post("/placement/grade", json={"answers": wrong})
    assert second.status_code == 200
    assert second.json()["level"] == "A1"

    map_resp = await client.get("/curriculum")
    assert map_resp.json()["placement_level"] == "A1"


async def test_grade_placement_invalid_body_returns_422(client: httpx.AsyncClient):
    resp = await client.post("/placement/grade", json={"answers": "nope"})
    assert resp.status_code == 422


async def test_retake_placement_preserves_module_progress(client: httpx.AsyncClient):
    # Complete a module first: read its lesson and attempt its quiz (§7 rule).
    await client.post("/curriculum/lessons/b1.grammar.articles/read")
    graded = await client.post(
        "/curriculum/quiz/grade",
        json={
            "module_id": "b1.grammar.articles",
            "answers": [
                {"item_id": "b1.grammar.articles.q1", "given": "0"},
                {"item_id": "b1.grammar.articles.q2", "given": "2"},
            ],
        },
    )
    assert graded.status_code == 200

    def _articles_module(body: dict[str, object]) -> dict[str, object]:
        levels = body["levels"]
        assert isinstance(levels, list)
        b1 = next(s for s in levels if s["level"] == "B1")
        return next(m for m in b1["modules"] if m["id"] == "b1.grammar.articles")

    before = _articles_module((await client.get("/curriculum")).json())
    assert before["status"] == "completed"

    # Retaking placement re-points the profile but must never wipe progress (§9).
    resp = await client.post("/placement/grade", json={"answers": _answers(list(ALL_CORRECT))})
    assert resp.status_code == 200

    after_body = (await client.get("/curriculum")).json()
    assert after_body["placement_level"] == "C1"
    after = _articles_module(after_body)
    assert after["status"] == "completed"
    assert after["quiz_best_score"] == before["quiz_best_score"]
