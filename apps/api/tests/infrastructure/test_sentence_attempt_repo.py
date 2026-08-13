from datetime import UTC, datetime

from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.sentence_attempt_repo import (
    SqlSentenceAttemptRepository,
)

NOW = datetime(2026, 8, 13, tzinfo=UTC)


async def _repo() -> SqlSentenceAttemptRepository:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    return SqlSentenceAttemptRepository(db)


async def test_add_assigns_id_and_list_roundtrips_feedback():
    repo = await _repo()
    fb = Feedback(
        verdict=Verdict.NEEDS_WORK, feedback="Tense.", corrected="I ran.", example="I run."
    )
    saved = await repo.add(SentenceAttempt.create(1, "I runned.", fb, NOW))
    assert saved.id is not None
    listed = await repo.list_for_card(1)
    assert len(listed) == 1
    assert listed[0].sentence == "I runned."
    assert listed[0].feedback == fb
    assert await repo.list_for_card(999) == []
