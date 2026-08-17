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
    assert body["has_quiz"] is False
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