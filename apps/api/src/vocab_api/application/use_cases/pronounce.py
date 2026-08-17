from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.application.ports.pronunciation import PronunciationScorer
from vocab_api.domain.pronunciation.assessment import PronunciationAssessment
from vocab_api.domain.shared.errors import EmptyAudio, EmptyPronunciationText, UnsupportedAccent


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
