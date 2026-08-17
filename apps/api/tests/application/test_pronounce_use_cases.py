import pytest

from vocab_api.application.errors import PronunciationUnavailable
from vocab_api.application.use_cases.pronounce import ScorePronunciation
from vocab_api.domain.pronunciation.assessment import (
    PhonemeScore,
    PronunciationAssessment,
    Verdict,
    WordScore,
)
from vocab_api.domain.shared.errors import EmptyAudio, EmptyPronunciationText, UnsupportedAccent
from vocab_api.infrastructure.pronunciation.null_scorer import NullScorer


class FakeScorer:
    """A canned scorer whose behaviour the test configures."""

    def __init__(self) -> None:
        self.calls: list[tuple[bytes, str, str]] = []
        self.raise_unavailable = False

    async def score(self, audio: bytes, target_text: str, accent: str) -> PronunciationAssessment:
        self.calls.append((audio, target_text, accent))
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


async def test_score_validates_audio():
    use_case = ScorePronunciation(FakeScorer(), NullScorer())
    with pytest.raises(EmptyAudio):
        await use_case.execute(b"", "hello")


async def test_score_validates_target():
    use_case = ScorePronunciation(FakeScorer(), NullScorer())
    with pytest.raises(EmptyPronunciationText):
        await use_case.execute(b"\x00audio", "   ")


async def test_score_validates_accent():
    use_case = ScorePronunciation(FakeScorer(), NullScorer())
    with pytest.raises(UnsupportedAccent):
        await use_case.execute(b"\x00audio", "hello", accent="ru-RU")


async def test_score_strips_target_and_uses_default_accent():
    fake = FakeScorer()
    use_case = ScorePronunciation(fake, NullScorer())
    result = await use_case.execute(b"\x00audio", "  hello  ")
    assert result.scored_phonemes is True
    assert result.overall == 0.9
    assert fake.calls == [(b"\x00audio", "hello", "en-US")]


async def test_provider_failure_degrades_to_fallback():
    fake = FakeScorer()
    fake.raise_unavailable = True
    use_case = ScorePronunciation(fake, NullScorer())
    result = await use_case.execute(b"\x00audio", "hello")
    assert result.scored_phonemes is False
    assert result.words == ()


async def test_null_scorer_never_raises_and_is_neutral():
    scorer = NullScorer()
    result = await scorer.score(b"", "hello", "en-US")
    assert result.scored_phonemes is False
    assert result.overall == 0.5
    assert result.words == ()
    assert result.transcript == ""
