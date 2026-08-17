from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.application.ports.pronunciation import PronunciationScorer
from vocab_api.domain.pronunciation.assessment import PronunciationAssessment
from vocab_api.domain.shared.errors import (
    AudioTooLarge,
    EmptyAudio,
    EmptyPronunciationText,
    UnsupportedAccent,
)

# A short spoken utterance is well under a megabyte; cap the upload so a rogue or
# runaway recording cannot exhaust memory (spec §7).
MAX_AUDIO_BYTES = 10 * 1024 * 1024


class ScorePronunciation:
    """Score a spoken utterance against a target text.

    Validates the request, asks the configured primary scorer, and on a
    ``PronunciationUnavailable`` degrades to a fallback scorer (NullScorer in
    the wired configuration, which never raises) so the learner always gets a
    response — never an error.
    """

    def __init__(self, scorer: PronunciationScorer, fallback: PronunciationScorer) -> None:
        self._scorer = scorer
        self._fallback = fallback

    async def execute(
        self, audio: bytes, target_text: str, accent: str = "en-US"
    ) -> PronunciationAssessment:
        if not audio:
            raise EmptyAudio()
        if len(audio) > MAX_AUDIO_BYTES:
            raise AudioTooLarge(len(audio), MAX_AUDIO_BYTES)
        target = target_text.strip()
        if not target:
            raise EmptyPronunciationText()
        accent = accent.strip()
        if not accent.startswith("en"):
            raise UnsupportedAccent(accent)
        try:
            return await self._scorer.score(audio, target, accent)
        except PronunciationUnavailable:
            return await self._fallback.score(audio, target, accent)
