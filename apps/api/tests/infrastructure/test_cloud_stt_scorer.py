import httpx
import pytest

from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.infrastructure.pronunciation.cloud_stt_scorer import (
    CloudSttScorer,
    match_words,
    overall_score,
)


def _client(payload: object, status_code: int = 200) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/transcribe")
        return httpx.Response(status_code, json=payload)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_match_words_flags_missing_words():
    words = match_words("i ran yesterday", "I run every day")
    assert [w.word for w in words] == ["i", "run", "every", "day"]
    assert [w.score for w in words] == [1.0, 0.0, 0.0, 0.0]
    assert all(w.phonemes == () for w in words)


async def test_match_words_empty_transcript():
    words = match_words("", "run")
    assert [w.word for w in words] == ["run"]
    assert [w.score for w in words] == [0.0]
    assert match_words("", "") == ()
    assert overall_score(()) == 0.0


async def test_overall_score_is_share_matched():
    words = match_words("run", "run every")
    assert overall_score(words) == pytest.approx(0.5)


async def test_cloud_scorer_scores_from_transcript():
    scorer = CloudSttScorer("http://cloud/", 15.0, client=_client({"text": "I ran yesterday."}))
    assessment = await scorer.score(b"audio", "I run every day", "en-US")
    assert assessment.scored_phonemes is False
    assert assessment.transcript == "I ran yesterday."
    assert [w.score for w in assessment.words] == [1.0, 0.0, 0.0, 0.0]


async def test_cloud_scorer_raises_on_bad_status():
    scorer = CloudSttScorer("http://cloud/", 15.0, client=_client({}, status_code=502))
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "run", "en-US")


async def test_cloud_scorer_raises_on_connect_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    scorer = CloudSttScorer(
        "http://cloud/", 15.0, client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    with pytest.raises(PronunciationUnavailable):
        await scorer.score(b"audio", "run", "en-US")


async def test_cloud_scorer_raises_on_malformed_json():
    scorer = CloudSttScorer("http://cloud/", 15.0, client=_client({"unexpected": True}))
    assessment = await scorer.score(b"audio", "run", "en-US")
    assert assessment.transcript == ""
    assert [w.score for w in assessment.words] == [0.0]
