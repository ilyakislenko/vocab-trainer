"""Cloud STT scorer: Whisper-style transcription → word-level match (degraded).

No phoneme scoring — ``scored_phonemes=False`` and empty phoneme lists. The
transcript is matched word-by-word against the target so the learner still gets
useful per-word feedback even when the GPU box is offline. Any upstream failure
surfaces as ``PronunciationUnavailable`` and the use case degrades to the
fallback scorer.
"""

import re

import httpx

from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.domain.pronunciation.assessment import (
    PronunciationAssessment,
    WordScore,
)


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z']+", text.casefold()))


def match_words(transcript: str, target: str) -> tuple[WordScore, ...]:
    """Match each target word against the transcribed tokens (exact, casefolded)."""
    heard = set(_tokens(transcript))
    return tuple(
        WordScore(
            word=word,
            score=1.0 if word in heard else 0.0,
            phonemes=(),
        )
        for word in _tokens(target)
    )


def overall_score(words: tuple[WordScore, ...]) -> float:
    if not words:
        return 0.0
    return sum(word.score for word in words) / len(words)


class CloudSttScorer:
    """Scores via a Whisper-style ``POST {base}/transcribe`` endpoint.

    The endpoint takes multipart ``audio`` (+ ``language``) and returns JSON
    ``{"text": "..."}``; the transcript is then matched word-by-word against the
    target. Expected to be configured behind the ``cloud`` provider.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._url = base_url.rstrip("/") + "/transcribe"
        self._timeout = timeout
        self._client = client

    async def score(self, audio: bytes, target_text: str, accent: str) -> PronunciationAssessment:
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.post(
                self._url,
                files={"audio": ("audio.webm", audio, "audio/webm")},
                data={"language": accent},
            )
            response.raise_for_status()
            transcript = str(response.json().get("text", ""))
        except (httpx.HTTPError, ValueError):
            raise PronunciationUnavailable() from None
        finally:
            if self._client is None:
                await client.aclose()
        words = match_words(transcript, target_text)
        return PronunciationAssessment(
            overall=overall_score(words),
            words=words,
            transcript=transcript,
            scored_phonemes=False,
        )
