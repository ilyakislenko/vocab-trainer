"""HTTP contract tests for the rtx service. Use a fake scorer (no model load)."""

import httpx
import pytest

from app import create_app


class FakeScorer:
    def score(self, wav_bytes: bytes, target_text: str) -> dict:
        return {
            "overall": 0.87,
            "words": [
                {
                    "word": "h ə l oʊ",
                    "score": 0.87,
                    "phonemes": [
                        {"phoneme": "h", "score": 0.9, "verdict": "good"},
                        {"phoneme": "oʊ", "score": 0.4, "verdict": "weak"},
                    ],
                }
            ],
            "transcript": "hello",
            "scored_phonemes": True,
        }


@pytest.fixture
def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app(FakeScorer()))
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_gop_returns_assessment(client):
    resp = await client.post(
        "/gop",
        data={"target": "hello"},
        files={"audio": ("audio.wav", b"fake-wav-bytes", "audio/wav")},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["scored_phonemes"] is True
    assert payload["overall"] == pytest.approx(0.87)
    assert payload["words"][0]["phonemes"][1]["verdict"] == "weak"


async def test_gop_rejects_empty_audio(client):
    resp = await client.post(
        "/gop",
        data={"target": "hello"},
        files={"audio": ("audio.wav", b"", "audio/wav")},
    )
    assert resp.status_code == 422


async def test_gop_rejects_empty_target(client):
    resp = await client.post(
        "/gop",
        data={"target": "   "},
        files={"audio": ("audio.wav", b"data", "audio/wav")},
    )
    assert resp.status_code == 422