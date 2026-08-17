"""Pure pronunciation-scoring value objects (no framework).

The GOP (Goodness of Pronunciation) score for a phoneme is a 0..1 value; the
``verdict_for`` function is the single pure mapping from a score to a
``Verdict``. Aggregation to word/overall scores is left to the scorers (the
GOP service computes them from the aligned posteriors); the verdict mapping
itself lives here so every backend reports comparable labels.
"""

from dataclasses import dataclass
from enum import StrEnum

GOOD_THRESHOLD = 0.8
WEAK_THRESHOLD = 0.5


class Verdict(StrEnum):
    GOOD = "good"
    FAIR = "fair"
    WEAK = "weak"


@dataclass(frozen=True, slots=True)
class PhonemeScore:
    phoneme: str
    score: float
    verdict: Verdict


@dataclass(frozen=True, slots=True)
class WordScore:
    word: str
    score: float
    phonemes: tuple[PhonemeScore, ...]


@dataclass(frozen=True, slots=True)
class PronunciationAssessment:
    overall: float
    words: tuple[WordScore, ...]
    transcript: str
    scored_phonemes: bool


def verdict_for(score: float) -> Verdict:
    """Map a 0..1 phoneme score to a verdict at the named thresholds."""
    if score >= GOOD_THRESHOLD:
        return Verdict.GOOD
    if score >= WEAK_THRESHOLD:
        return Verdict.FAIR
    return Verdict.WEAK
