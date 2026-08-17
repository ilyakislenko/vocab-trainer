from vocab_api.domain.pronunciation.assessment import PronunciationAssessment


class NullScorer:
    """Offline self-check scorer: always returns a valid, neutral assessment
    and never raises.

    ``scored_phonemes`` is False — the response tells the frontend that no
    phoneme scoring happened, so it falls back to the word-match view. The
    transcript is empty because nothing was actually transcribed; the browser
    STT fallback supplies the heard text client-side.
    """

    async def score(self, audio: bytes, target_text: str, accent: str) -> PronunciationAssessment:
        return PronunciationAssessment(
            overall=0.5,
            words=(),
            transcript="",
            scored_phonemes=False,
        )
