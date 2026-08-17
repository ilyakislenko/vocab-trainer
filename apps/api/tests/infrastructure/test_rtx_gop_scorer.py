import httpx
import pytest

from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.infrastructure.pronunciation.rtx_gop_scorer import RtxGopScorer


async def _passthrough(audio: bytes) -> bytes:
    return audio


def _full_payload() -> dict:
    return {
        "overall": 0.87,
        "words": [
            {
                "word": "hello",
                "score": 0.87,
                "phonemes": [
                    {"phoneme": "h", "score": 0.9, "verdict": "good"},
                    {"phoneme": "l", "score": 0.4, "verdict": "weak"},
                ],
            }
        ],
        "transcript": "hello",
        "scored_phonemes": True,
    }


def _client(payload: object, health_status: int = 200, gop_status: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/healthz"):
            return httpx.Response(health_status)
        if request.url.path.endswith("/gop"):
            return httpx.Response(gop_status, json=payload)
        return httpx.Response(404)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_rtx_scorer_parses_full_gop_assessment():
    scorer = RtxGopScorer(
        "http://rtx:8900",
        15.0,
        client=_client(_full_payload()),
        converter=_passthrough,
    )
    assessment = await scorer.score(b"not-a-real-wav", "hello", "en-US")
    assert assessment.scored_phonemes is True
    assert assessment.overall == pytest.approx(0.87)
    word = assessment.words[0]
    assert word.word == "hello"
    assert [p.phoneme for p in word.phonemes] == ["h", "l"]
    assert word.phonemes[0].verdict.value == "good"
    assert word.phonemes[1].verdict.value == "weak"


async def test_rtx_scorer_fails_fast_when_healthz_is_down():
    scorer = RtxGopScorer(
        "http://rtx:8900",
        15.0,
        client=_client(_full_payload(), health_status=500),
        converter=_passthrough,
    )
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "hello", "en-US")


async def test_rtx_scorer_raises_on_gop_error():
    scorer = RtxGopScorer(
        "http://rtx:8900",
        15.0,
        client=_client(_full_payload(), gop_status=502),
        converter=_passthrough,
    )
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "hello", "en-US")


async def test_rtx_scorer_raises_on_connect_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sleeping", request=request)

    scorer = RtxGopScorer(
        "http://rtx:8900",
        15.0,
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        converter=_passthrough,
    )
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "hello", "en-US")


async def test_rtx_scorer_raises_on_malformed_gop_payload():
    scorer = RtxGopScorer(
        "http://rtx:8900",
        15.0,
        client=_client({"nope": True}),
        converter=_passthrough,
    )
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "hello", "en-US")


async def test_rtx_scorer_raises_when_ffmpeg_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _name: None)
    scorer = RtxGopScorer(
        "http://rtx:8900",
        15.0,
        client=_client(_full_payload()),
    )
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "hello", "en-US")
