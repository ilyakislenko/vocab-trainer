"""HTTP client for the rtx GOP inference service (full phoneme scoring).

Thin client only — no torch/transformers here. Converts the incoming audio to
16 kHz mono wav via ffmpeg (the service contract), probes ``GET /healthz`` to
fail fast when the box is asleep/off, then ``POST /gop``. Any failure raises
``PronunciationUnavailable``; the use case degrades to the fallback scorer.
"""

import asyncio
import shutil
from collections.abc import Awaitable, Callable

import httpx

from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.domain.pronunciation.assessment import (
    PhonemeScore,
    PronunciationAssessment,
    Verdict,
    WordScore,
)

_VERDICTS = {
    Verdict.GOOD.value: Verdict.GOOD,
    Verdict.FAIR.value: Verdict.FAIR,
    Verdict.WEAK.value: Verdict.WEAK,
}


class RtxGopScorer:
    """Scores via the LAN rtx inference service (``POST /gop``)."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        connect_timeout: float = 2.0,
        client: httpx.AsyncClient | None = None,
        converter: Callable[[bytes], Awaitable[bytes]] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout, connect=connect_timeout)
        self._client = client
        self._converter = converter or self._convert_with_ffmpeg

    @staticmethod
    def _parse(payload: object) -> PronunciationAssessment:
        if not isinstance(payload, dict) or "words" not in payload:
            raise ValueError("unexpected /gop payload")
        words = tuple(
            WordScore(
                word=str(word.get("word", "")),
                score=float(word["score"]),
                phonemes=tuple(
                    PhonemeScore(
                        phoneme=str(phoneme["phoneme"]),
                        score=float(phoneme["score"]),
                        verdict=_VERDICTS[str(phoneme["verdict"])],
                    )
                    for phoneme in word.get("phonemes", ())
                ),
            )
            for word in payload["words"]
        )
        return PronunciationAssessment(
            overall=float(payload["overall"]),
            words=words,
            transcript=str(payload.get("transcript", "")),
            scored_phonemes=bool(payload.get("scored_phonemes", True)),
        )

    async def score(self, audio: bytes, target_text: str, accent: str) -> PronunciationAssessment:
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            health = await client.get(f"{self._base_url}/healthz")
            if health.status_code != 200:
                raise PronunciationUnavailable()
            wav = await self._convert(audio)
            response = await client.post(
                f"{self._base_url}/gop",
                files={"audio": ("audio.wav", wav, "audio/wav")},
                data={"target": target_text, "accent": accent},
            )
            response.raise_for_status()
            return self._parse(response.json())
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise PronunciationUnavailable() from None
        finally:
            if self._client is None:
                await client.aclose()

    async def _convert(self, audio: bytes) -> bytes:
        return await self._converter(audio)

    async def _convert_with_ffmpeg(self, audio: bytes) -> bytes:
        binary = shutil.which("ffmpeg")
        if binary is None:
            raise PronunciationUnavailable()
        try:
            proc = await asyncio.create_subprocess_exec(
                binary,
                "-i",
                "pipe:0",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "wav",
                "pipe:1",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except OSError:
            raise PronunciationUnavailable() from None
        stdout, _ = await proc.communicate(audio)
        if proc.returncode != 0 or not stdout:
            raise PronunciationUnavailable()
        return stdout
