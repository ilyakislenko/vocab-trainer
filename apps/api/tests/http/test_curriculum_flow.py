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


async def test_curriculum_map_lists_all_levels(client: httpx.AsyncClient):
    resp = await client.get("/curriculum")
    assert resp.status_code == 200
    body = resp.json()
    levels = body["levels"]
    assert [section["level"] for section in levels] == ["A1", "A2", "B1", "B2", "C1", "C2"]
    b1 = next(s for s in levels if s["level"] == "B1")
    module = next(m for m in b1["modules"] if m["id"] == "b1.grammar.articles")
    assert module["title"] == "Articles: a/an, the, zero article"
    assert module["level"] == "B1"
    assert module["track"] == "grammar"
    assert module["availability"] == "available"
    assert module["status"] == "not_started"
    assert body["recommended_module_id"] == "b1.grammar.articles"


async def test_curriculum_map_marks_lesson_read(client: httpx.AsyncClient):
    mark = await client.post("/curriculum/lessons/b1.grammar.articles/read")
    assert mark.status_code == 200
    assert mark.json()["status"] == "in_progress"

    resp = await client.get("/curriculum")
    b1 = next(s for s in resp.json()["levels"] if s["level"] == "B1")
    module = next(m for m in b1["modules"] if m["id"] == "b1.grammar.articles")
    assert module["status"] == "in_progress"


async def test_module_detail_for_available_module(client: httpx.AsyncClient):
    resp = await client.get("/curriculum/modules/b1.grammar.articles")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "b1.grammar.articles"
    assert body["level"] == "B1"
    assert body["track"] == "grammar"
    assert body["status"] == "not_started"
    assert body["has_quiz"] is True
    assert body["objectives"]
    assert body["references"]


async def test_module_detail_for_missing_module_returns_404(client: httpx.AsyncClient):
    resp = await client.get("/curriculum/modules/x1.missing.slug")
    assert resp.status_code == 404


async def test_lesson_returns_markdown_and_meta(client: httpx.AsyncClient):
    resp = await client.get("/curriculum/lessons/b1.grammar.articles")
    assert resp.status_code == 200
    body = resp.json()
    assert "# Articles" in body["markdown"]
    assert body["meta"]["id"] == "b1.grammar.articles"
    assert body["meta"]["level"] == "B1"
    assert body["meta"]["track"] == "grammar"
    assert body["meta"]["estimated_minutes"] == 8
    assert body["meta"]["skills"]


async def test_lesson_for_missing_module_returns_404(client: httpx.AsyncClient):
    resp = await client.get("/curriculum/lessons/x1.missing.slug")
    assert resp.status_code == 404


async def test_mark_lesson_read_is_idempotent(client: httpx.AsyncClient):
    first = await client.post("/curriculum/lessons/b1.grammar.articles/read")
    second = await client.post("/curriculum/lessons/b1.grammar.articles/read")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "in_progress"
    assert second.json()["status"] == "in_progress"
    assert first.json()["lesson_read_at"] == second.json()["lesson_read_at"]


async def test_mark_lesson_read_for_missing_module_returns_404(client: httpx.AsyncClient):
    resp = await client.post("/curriculum/lessons/x1.missing.slug/read")
    assert resp.status_code == 404


async def test_quiz_returns_items_without_answers(client: httpx.AsyncClient):
    resp = await client.get("/curriculum/modules/b1.grammar.articles/quiz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["module_id"] == "b1.grammar.articles"
    assert body["status"] == "not_started"
    items = body["items"]
    assert len(items) == 6
    types = {item["type"] for item in items}
    assert {"mcq", "cloze", "error_correction"} <= types
    for item in items:
        assert item["id"]
        assert item["skill"]
        assert item["prompt"]
        assert "answer_index" not in item
        assert "answers" not in item
        assert "explanation" not in item
        if item["type"] == "mcq":
            assert item["options"]
        else:
            assert item["options"] is None


async def test_quiz_for_missing_module_returns_404(client: httpx.AsyncClient):
    resp = await client.get("/curriculum/modules/x1.missing.slug/quiz")
    assert resp.status_code == 404


async def test_grade_quiz_grades_deterministically_and_completes(client: httpx.AsyncClient):
    mark = await client.post("/curriculum/lessons/b1.grammar.articles/read")
    assert mark.status_code == 200
    answers = [
        {"item_id": "b1.grammar.articles.q1", "given": "0"},
        {"item_id": "b1.grammar.articles.q2", "given": "2"},
        {"item_id": "b1.grammar.articles.q3", "given": "3"},
        {"item_id": "b1.grammar.articles.q4", "given": "the"},
        {"item_id": "b1.grammar.articles.q5", "given": "a"},
        {"item_id": "b1.grammar.articles.q6", "given": "I go to work by train every day"},
    ]
    resp = await client.post(
        "/curriculum/quiz/grade",
        json={"module_id": "b1.grammar.articles", "answers": answers},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["module_id"] == "b1.grammar.articles"
    assert result["status"] == "completed"
    assert result["completed"] is True
    assert result["score"] == pytest.approx(5 / 6 * 100)
    assert result["next_module_id"] == "b1.grammar.perfect-aspect"
    by_id = {item["item_id"]: item for item in result["items"]}
    assert len(result["items"]) == 6
    assert by_id["b1.grammar.articles.q1"]["correct"] is True
    assert by_id["b1.grammar.articles.q5"]["correct"] is False
    assert by_id["b1.grammar.articles.q5"]["explanation"]
    assert by_id["b1.grammar.articles.q6"]["correct"] is True


async def test_grade_quiz_without_lesson_read_does_not_complete(
    client: httpx.AsyncClient,
):
    answers = [{"item_id": "b1.grammar.articles.q1", "given": "0"}]
    resp = await client.post(
        "/curriculum/quiz/grade",
        json={"module_id": "b1.grammar.articles", "answers": answers},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["completed"] is False
    assert result["status"] == "not_started"


async def test_grade_quiz_ignores_unknown_item_ids(client: httpx.AsyncClient):
    answers = [
        {"item_id": "b1.grammar.articles.q1", "given": "0"},
        {"item_id": "b1.grammar.articles.does-not-exist", "given": "whatever"},
    ]
    resp = await client.post(
        "/curriculum/quiz/grade",
        json={"module_id": "b1.grammar.articles", "answers": answers},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert len(result["items"]) == 1
    assert result["items"][0]["item_id"] == "b1.grammar.articles.q1"


async def test_grade_quiz_for_missing_module_returns_404(client: httpx.AsyncClient):
    resp = await client.post(
        "/curriculum/quiz/grade",
        json={"module_id": "x1.missing.slug", "answers": []},
    )
    assert resp.status_code == 404


async def test_quiz_best_score_reflected_on_map(client: httpx.AsyncClient):
    answers = [
        {"item_id": "b1.grammar.articles.q1", "given": "0"},
        {"item_id": "b1.grammar.articles.q2", "given": "2"},
        {"item_id": "b1.grammar.articles.q3", "given": "3"},
        {"item_id": "b1.grammar.articles.q4", "given": "wrong"},
        {"item_id": "b1.grammar.articles.q5", "given": "wrong"},
        {"item_id": "b1.grammar.articles.q6", "given": "wrong"},
    ]
    resp = await client.post(
        "/curriculum/quiz/grade",
        json={"module_id": "b1.grammar.articles", "answers": answers},
    )
    assert resp.status_code == 200
    assert resp.json()["score"] == pytest.approx(50.0)

    resp = await client.get("/curriculum")
    b1 = next(s for s in resp.json()["levels"] if s["level"] == "B1")
    module = next(m for m in b1["modules"] if m["id"] == "b1.grammar.articles")
    assert module["quiz_best_score"] == pytest.approx(50.0)


async def test_grade_quiz_creates_skill_items_for_failures(client: httpx.AsyncClient):
    answers = [
        {"item_id": "b1.grammar.articles.q1", "given": "99"},
        {"item_id": "b1.grammar.articles.q4", "given": "wrong"},
    ]
    resp = await client.post(
        "/curriculum/quiz/grade",
        json={"module_id": "b1.grammar.articles", "answers": answers},
    )
    assert resp.status_code == 200
    by_id = {item["item_id"]: item for item in resp.json()["items"]}
    assert by_id["b1.grammar.articles.q1"]["correct"] is False
    assert by_id["b1.grammar.articles.q4"]["correct"] is False

    resp = await client.get("/review/skills/queue?limit=20")
    assert resp.status_code == 200
    queue = resp.json()
    skills = {item["skill"] for item in queue}
    assert "art.indefinite" in skills
    assert "art.definite" in skills
    for item in queue:
        assert item["id"] > 0
        assert item["module_id"] == "b1.grammar.articles"
        assert item["source_item_id"]
        assert item["prompt"]
        assert item["explanation"]
        assert item["answers"]
        assert item["is_leech"] is False


async def test_skill_review_queue_respects_limit_and_advances(client: httpx.AsyncClient):
    await client.post(
        "/curriculum/quiz/grade",
        json={
            "module_id": "b1.grammar.articles",
            "answers": [{"item_id": "b1.grammar.articles.q1", "given": "99"}],
        },
    )
    queue = (await client.get("/review/skills/queue?limit=1")).json()
    assert len(queue) == 1
    item = queue[0]
    assert item["skill"] == "art.indefinite"
    assert item["type"] == "mcq"
    assert item["answers"] == ["a"]

    resp = await client.post(
        "/review/skills", json={"skill_item_id": item["id"], "rating": 3}
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == item["id"]
    assert resp.json()["is_leech"] is False


async def test_skill_review_missing_item_returns_404(client: httpx.AsyncClient):
    resp = await client.post("/review/skills", json={"skill_item_id": 99999, "rating": 3})
    assert resp.status_code == 404


async def test_skill_review_invalid_rating_returns_422(client: httpx.AsyncClient):
    resp = await client.post("/review/skills", json={"skill_item_id": 1, "rating": 7})
    assert resp.status_code == 422


async def test_focus_lists_leeches(client: httpx.AsyncClient):
    await client.post(
        "/curriculum/quiz/grade",
        json={
            "module_id": "b1.grammar.articles",
            "answers": [{"item_id": "b1.grammar.articles.q1", "given": "99"}],
        },
    )
    item = (await client.get("/review/skills/queue?limit=1")).json()[0]

    assert (await client.get("/session/focus")).json() == []

    # Graduate the item into Review state, then fail it four times.
    for rating in (3, 3, 1, 1, 1, 1):
        resp = await client.post(
            "/review/skills",
            json={"skill_item_id": item["id"], "rating": rating},
        )
        assert resp.status_code == 200

    focus = (await client.get("/session/focus")).json()
    assert len(focus) == 1
    assert focus[0]["skill"] == "art.indefinite"
    assert focus[0]["is_leech"] is True