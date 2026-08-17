from vocab_api.domain.pronunciation.assessment import (
    GOOD_THRESHOLD,
    WEAK_THRESHOLD,
    Verdict,
    verdict_for,
)


def test_verdict_for_good_at_and_above_threshold():
    assert verdict_for(GOOD_THRESHOLD) is Verdict.GOOD
    assert verdict_for(1.0) is Verdict.GOOD


def test_verdict_for_fair_between_thresholds():
    assert verdict_for(WEAK_THRESHOLD) is Verdict.FAIR
    assert verdict_for((GOOD_THRESHOLD + WEAK_THRESHOLD) / 2) is Verdict.FAIR


def test_verdict_for_weak_below_threshold():
    assert verdict_for(0.0) is Verdict.WEAK
    assert verdict_for(WEAK_THRESHOLD - 0.01) is Verdict.WEAK


def test_verdict_edge_boundaries():
    assert verdict_for(GOOD_THRESHOLD - 0.01) is Verdict.FAIR
    assert verdict_for(WEAK_THRESHOLD + 0.01) is Verdict.FAIR
