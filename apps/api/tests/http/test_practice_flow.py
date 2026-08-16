import httpx
import pytest

from vocab_api.application.errors import LlmUnavailable
from vocab_api.application.use_cases.practice import (
    CheckSentence,
    ConductInterview,
    DescribeWord,
    DrillWord,
    SelectTopicWords,
)
from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.interview import InterviewEvaluation, InterviewQuestion
from vocab_api.domain.practice.word_hint import WordHint
from vocab_api.main import create_app


class RaisingLlm:
    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        raise LlmUnavailable("The language model is unavailable.")

    async def suggest_example(self, word: str) -> str:
        raise LlmUnavailable("The language model is unavailable.")

    async def select_topic_words(self, topic: str, limit: int) -> list[str]:
        raise LlmUnavailable("The language model is unavailable.")

    async def describe_word(self, word: str) -> WordHint:
        raise LlmUnavailable("The language model is unavailable.")

    async def interview(
        self, topic: str, lang: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        raise LlmUnavailable("The language model is unavailable.")


class TopicLlm:
    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        return Feedback(verdict=Verdict.OK, feedback="Good.")

    async def suggest_example(self, word: str) -> str:
        return f"Word: {word}."

    async def select_topic_words(self, topic: str, limit: int) -> list[str]:
        return ["run", "jump", "absent"]

    async def describe_word(self, word: str) -> WordHint:
        return WordHint(meaning=f"Значение {word}.", example=f"I {word} daily.")

    async def drill_word(self, word: str, user_message: str) -> tuple[str, str]:
        return f"Nice use of '{word}'!", f"Can you use '{word}' in another sentence?"

    async def interview(
        self, topic: str, lang: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        if not messages:
            return InterviewEvaluation(verdict=None, feedback=None, corrected=None)
        return InterviewEvaluation(
            verdict=Verdict.OK,
            feedback="Хороший ответ.",
            corrected="A better answer.",
        )


class FollowUpLlm:
    async def interview(
        self, topic: str, lang: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        if not messages:
            return InterviewEvaluation(verdict=None, feedback=None, corrected=None)
        if lang == "ru":
            return InterviewEvaluation(
                verdict=Verdict.OK,
                feedback="Хороший ответ.",
                corrected="A better answer.",
                advance=False,
                next_question="Расскажи подробнее?",
            )
        return InterviewEvaluation(
            verdict=Verdict.OK,
            feedback="Хороший ответ.",
            corrected="A better answer.",
            advance=False,
            next_question="Can you elaborate?",
        )


class AdvancingLlm:
    async def interview(
        self, topic: str, lang: str, messages: list[dict[str, str]]
    ) -> InterviewEvaluation:
        if not messages:
            return InterviewEvaluation(verdict=None, feedback=None, corrected=None)
        return InterviewEvaluation(
            verdict=Verdict.OK,
            feedback="Хороший ответ.",
            corrected="A better answer.",
            advance=True,
            next_question=None,
        )


class StubQuestionBank:
    def __init__(self) -> None:
        self._questions = [
            InterviewQuestion(
                id=1,
                topics=("React",),
                level="Middle",
                ru="Что такое props?",
                en="What are props?",
            ),
            InterviewQuestion(
                id=2,
                topics=("React",),
                level="Middle",
                ru="Что такое state?",
                en="What is state?",
            ),
        ]

    def next(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion:
        matching = [q for q in self._questions if topic in q.topics]
        if not matching:
            raise ValueError(f"No interview questions for topic {topic!r}")
        unused = [q for q in matching if q.id not in used_question_ids]
        return min(unused or matching, key=lambda q: q.id)

    def random(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion:
        matching = [q for q in self._questions if topic in q.topics]
        if not matching:
            raise ValueError(f"No interview questions for topic {topic!r}")
        unused = [q for q in matching if q.id not in used_question_ids]
        return (unused or matching)[0]


@pytest.fixture
async def client():
    # llm_provider defaults to "none"
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
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
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
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


async def test_topic_returns_cards_matching_llm_words():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.select_topic_words = SelectTopicWords(container.select_topic_words._cards, TopicLlm())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        deck = (await client.post("/decks", json={"name": "T"})).json()
        await client.post(
            f"/decks/{deck['id']}/import",
            json={
                "raw": "run,бежать\njump,прыгать\ntrain,поезд",
                "format": "csv",
                "dry_run": False,
            },
        )
        resp = await client.get(
            "/practice/topic",
            params={"deck_id": deck["id"], "topic": "travel", "limit": 10},
        )
    assert resp.status_code == 200
    assert {c["word"] for c in resp.json()} == {"run", "jump"}


async def test_topic_with_null_provider_returns_empty():
    # Uses the default container (llm_provider="none"): NullProvider yields no
    # topic words, so the endpoint returns an empty list rather than an error.
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        deck = (await client.post("/decks", json={"name": "T"})).json()
        await client.post(
            f"/decks/{deck['id']}/import",
            json={"raw": "run,бежать", "format": "csv", "dry_run": False},
        )
        resp = await client.get(
            "/practice/topic", params={"deck_id": deck["id"], "topic": "travel", "limit": 10}
        )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_hint_returns_llm_description():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.describe_word = DescribeWord(container.describe_word._cards, TopicLlm())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        deck = (await client.post("/decks", json={"name": "T"})).json()
        await client.post(
            f"/decks/{deck['id']}/import",
            json={"raw": "run,бежать", "format": "csv", "dry_run": False},
        )
        queue = await client.get("/review/queue", params={"deck_id": deck["id"], "limit": 5})
        card = queue.json()[0]
        resp = await client.get("/practice/hint", params={"card_id": card["id"]})
    assert resp.status_code == 200
    assert resp.json() == {"meaning": "Значение run.", "example": "I run daily."}


async def test_hint_with_null_provider_does_not_error():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        deck = (await client.post("/decks", json={"name": "T"})).json()
        await client.post(
            f"/decks/{deck['id']}/import",
            json={"raw": "run,бежать", "format": "csv", "dry_run": False},
        )
        queue = await client.get("/review/queue", params={"deck_id": deck["id"], "limit": 5})
        card = queue.json()[0]
        resp = await client.get("/practice/hint", params={"card_id": card["id"]})
    assert resp.status_code == 200
    assert resp.json()["meaning"]


async def test_hint_missing_card_404(client: httpx.AsyncClient):
    resp = await client.get("/practice/hint", params={"card_id": 999})
    assert resp.status_code == 404


async def test_drill_returns_response_and_question():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.drill_word = DrillWord(container.drill_word._cards, TopicLlm())
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
            "/practice/drill", json={"card_id": card["id"], "message": "I run every day"}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "run" in body["response"].lower()
    assert body["question"]


async def test_drill_missing_card_404(client: httpx.AsyncClient):
    resp = await client.post("/practice/drill", json={"card_id": 999, "message": "hi"})
    assert resp.status_code == 404


async def test_drill_with_null_provider_does_not_error():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
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
            "/practice/drill", json={"card_id": card["id"], "message": "I run"}
        )
    assert resp.status_code == 200
    assert "run" in resp.json()["response"].lower()


async def test_interview_returns_bank_question():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(TopicLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/practice/interview", json={"topic": "React", "messages": []})
    assert resp.status_code == 200
    assert resp.json()["question"] == "What are props?"
    assert resp.json()["question_id"] == 1
    assert resp.json()["verdict"] is None
    assert resp.json()["feedback"] is None


async def test_interview_evaluates_answer_and_asks_next_bank_question():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(TopicLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={
                "topic": "React",
                "used_question_ids": [1],
                "messages": [
                    {"role": "interviewer", "content": "What are props?"},
                    {"role": "user", "content": "A component is a function."},
                ],
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "ok"
    assert body["feedback"] == "Хороший ответ."
    assert body["corrected"] == "A better answer."
    assert body["question"] == "What is state?"
    assert body["question_id"] == 2


async def test_interview_keeps_discussing_with_llm_followup():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(FollowUpLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={
                "topic": "React",
                "lang": "en",
                "used_question_ids": [1],
                "messages": [
                    {"role": "interviewer", "content": "What are props?"},
                    {"role": "user", "content": "A component is a function."},
                ],
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "ok"
    assert body["question"] == "Can you elaborate?"
    assert body["question_id"] is None


async def test_interview_followup_localizes_to_ru():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(FollowUpLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={
                "topic": "React",
                "lang": "ru",
                "used_question_ids": [1],
                "messages": [
                    {"role": "interviewer", "content": "Что такое props?"},
                    {"role": "user", "content": "Компонент это функция."},
                ],
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question"] == "Расскажи подробнее?"
    assert body["question_id"] is None


async def test_interview_advances_to_bank_when_llm_asks():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(AdvancingLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={
                "topic": "React",
                "used_question_ids": [1],
                "messages": [
                    {"role": "interviewer", "content": "What are props?"},
                    {"role": "user", "content": "next"},
                ],
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question"] == "What is state?"
    assert body["question_id"] == 2


async def test_interview_mode_next_returns_bank_question():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(TopicLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={"topic": "React", "mode": "next", "used_question_ids": [1], "messages": []},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question"] == "What is state?"
    assert body["question_id"] == 2
    assert body["verdict"] is None


async def test_interview_mode_random_returns_bank_question():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(TopicLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={"topic": "React", "mode": "random", "messages": []},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question_id"] in {1, 2}
    assert body["verdict"] is None


async def test_interview_localizes_to_ru():
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    await container.init()
    container.conduct_interview = ConductInterview(TopicLlm(), StubQuestionBank())
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/practice/interview",
            json={"topic": "React", "lang": "ru", "messages": []},
        )
    assert resp.status_code == 200
    assert resp.json()["question"] == "Что такое props?"


async def test_interview_with_null_provider_does_not_error(client: httpx.AsyncClient):
    resp = await client.post("/practice/interview", json={"topic": "React", "messages": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["question"]
    assert body["question_id"] >= 1
    assert body["verdict"] is None


async def test_interview_empty_topic_422(client: httpx.AsyncClient):
    resp = await client.post("/practice/interview", json={"topic": "  ", "messages": []})
    assert resp.status_code == 422
