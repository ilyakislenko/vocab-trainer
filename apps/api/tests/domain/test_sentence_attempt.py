from datetime import UTC, datetime

import pytest

from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.domain.shared.errors import EmptySentence

NOW = datetime(2026, 8, 13, tzinfo=UTC)
FB = Feedback(verdict=Verdict.OK, feedback="Great.")


def test_create_trims_and_sets_created_at():
    attempt = SentenceAttempt.create(1, "  I run daily.  ", FB, NOW)
    assert attempt.sentence == "I run daily."
    assert attempt.feedback is FB
    assert attempt.created_at == NOW
    assert attempt.id is None


def test_blank_sentence_rejected():
    with pytest.raises(EmptySentence):
        SentenceAttempt.create(1, "   ", FB, NOW)


def test_verdict_values():
    assert (Verdict.OK, Verdict.NEEDS_WORK) == ("ok", "needs_work")
