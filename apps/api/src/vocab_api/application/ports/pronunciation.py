from typing import Protocol

from vocab_api.domain.pronunciation.assessment import PronunciationAssessment


class PronunciationScorer(Protocol):
    """Scores a spoken utterance against a target text.

    Implementations are backend-specific (rtx GOP service, cloud STT, null);
    the use case depends only on this port. A scorer raises
    ``PronunciationUnavailable`` when it cannot fulfil the request — never a
    framework exception.
    """

    async def score(
        self, audio: bytes, target_text: str, accent: str
    ) -> PronunciationAssessment: ...
