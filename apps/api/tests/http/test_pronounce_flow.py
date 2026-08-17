import httpx
import pytest

from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.application.use_cases.pronounce import ScorePronunciation
from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.domain.pronunciation.assessment import (
    PhonemeScore,
    PronunciationAssessment,
    Verdict,
    WordScore,
)
from vocab_api.infrastructure.pronunciation.null_scorer import NullScorer
from vocab_api.main import create_app


class FakeScorer:
    def __init__(self) -> None:
        self.raise_unavailable = False

    async def score(self, audio: bytes, target_text: str, accent: str) -> PronunciationAssessment:
        if self.raise_unavailable:
            raise PronunciationUnavailable("backend down")
        return PronunciationAssessment(
            overall=0.9,
            words=(
                WordScore(
                    word="hello",
                    score=0.9,
                    phonemes=(PhonemeScore(phoneme="h", score=0.9, verdict=Verdict.GOOD),),
                ),
            ),
            transcript="hello",
            scored_phonemes=True,
        )


@pytest.fixture
async def client():
    fake = FakeScorer()
    container = Container(
        Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            llm_provider="none",
            seed_default_deck=False,
        )
    )
    container.score_pronunciation = ScorePronunciation(fake, NullScorer())
    await container.init()
    app = create_app(container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, fake
    await container.dispose()


async def test_score_returns_full_assessment(client):
    c, _ = client
    resp = await c.post(
        "/pronounce/score",
        data={"target": "hello"},
        files={"audio": ("a.webm", b"\x00audio\x00", "audio/webm")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored_phonemes"] is True
    assert body["overall"] == 0.9
    assert body["transcript"] == "hello"
    assert body["words"][0]["word"] == "hello"
    assert body["words"][0]["phonemes"][0]["verdict"] == "good"


async def test_score_422_on_empty_audio(client):
    c, _ = client
    resp = await c.post(
        "/pronounce/score",
        data={"target": "hello"},
        files={"audio": ("a.webm", b"", "audio/webm")},
    )
    assert resp.status_code == 422


async def test_score_422_on_empty_target(client):
    c, _ = client
    resp = await c.post(
        "/pronounce/score",
        data={"target": "  "},
        files={"audio": ("a.webm", b"\x00audio", "audio/webm")},
    )
    assert resp.status_code == 422


async def test_score_422_on_unsupported_accent(client):
    c, _ = client
    resp = await c.post(
        "/pronounce/score",
        data={"target": "hello", "accent": "ru-RU"},
        files={"audio": ("a.webm", b"\x00audio", "audio/webm")},
    )
    assert resp.status_code == 422


async def test_score_degrades_to_200_on_provider_failure(client):
    c, fake = client
    fake.raise_unavailable = True
    resp = await c.post(
        "/pronounce/score",
        data={"target": "hello"},
        files={"audio": ("a.webm", b"\x00audio", "audio/webm")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored_phonemes"] is False
    assert body["words"] == []
