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


# The correct given value for every item in the placement bank lives in
# `tests/http/_placement_bank.py`. The bank is larger than one diagnostic, so
# tests fetch the sampled diagnostic and answer whatever was sampled
# (spec D1: selection randomizes per attempt).


async def test_placement_returns_a_sampled_diagnostic_without_answers(
    client: httpx.AsyncClient,
):
    items = await fetch_diagnostic(client)
    assert len(items) == 24
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
    assert all(count == 6 for count in by_level.values())


async def test_grade_placement_all_correct_gives_c1(client: httpx.AsyncClient):
    items = await fetch_diagnostic(client)
    resp = await client.post("/placement/grade", json={"answers": correct_answers(items)})
    assert resp.status_code == 200
    result = resp.json()
    assert result["level"] == "C1"
    assert result["current_module_id"] == "c1.grammar.cleft-sentences"
    assert all(r["correct"] for r in result["results"])
    assert len(result["results"]) == len(items)

    map_resp = await client.get("/curriculum")
    assert map_resp.json()["placement_level"] == "C1"


async def test_grade_placement_defaults_to_a1(client: httpx.AsyncClient):
    items = await fetch_diagnostic(client)
    wrong = correct_answers(items, correct=False)
    resp = await client.post("/placement/grade", json={"answers": wrong})
    assert resp.status_code == 200
    result = resp.json()
    assert result["level"] == "A1"
    # Default placement starts at the very first module of the ladder.
    assert result["current_module_id"] == "a1.grammar.to-be"
    assert all(not r["correct"] for r in result["results"])


async def test_grade_placement_returns_highest_passing_level(client: httpx.AsyncClient):
    items = await fetch_diagnostic(client)
    lower = [item for item in items if item["id"].startswith(("pl.a2.", "pl.b1."))]
    upper = [item for item in items if item["id"].startswith(("pl.b2.", "pl.c1."))]
    answers = correct_answers(lower) + correct_answers(upper, correct=False)
    resp = await client.post("/placement/grade", json={"answers": answers})
    assert resp.status_code == 200
    result = resp.json()
    assert result["level"] == "B1"
    assert result["current_module_id"] == "b1.grammar.articles"


async def test_grade_placement_returns_per_item_review(client: httpx.AsyncClient):
    items = await fetch_diagnostic(client)
    answers = correct_answers(items)
    answers[0]["given"] = "bogus"
    resp = await client.post("/placement/grade", json={"answers": answers})
    assert resp.status_code == 200
    first = resp.json()["results"][0]
    assert set(first) == {
        "item_id",
        "level",
        "skill",
        "prompt",
        "given",
        "correct",
        "correct_answer",
        "explanation",
    }
    assert first["given"] == "bogus"
    assert first["correct"] is False
    assert first["correct_answer"]
    assert first["explanation"]


async def test_grade_placement_is_retakeable(client: httpx.AsyncClient):
    items = await fetch_diagnostic(client)
    first = await client.post("/placement/grade", json={"answers": correct_answers(items)})
    assert first.json()["level"] == "C1"

    second = await client.post(
        "/placement/grade", json={"answers": correct_answers(items, correct=False)}
    )
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
    items = await fetch_diagnostic(client)
    resp = await client.post("/placement/grade", json={"answers": correct_answers(items)})
    assert resp.status_code == 200

    after_body = (await client.get("/curriculum")).json()
    assert after_body["placement_level"] == "C1"
    after = _articles_module(after_body)
    assert after["status"] == "completed"
    assert after["quiz_best_score"] == before["quiz_best_score"]
