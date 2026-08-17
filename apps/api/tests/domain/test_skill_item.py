from datetime import UTC, datetime

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.curriculum.skill_item import LEECH_LAPSES, SkillItem

NOW = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)


def test_create_initialises_due_now():
    item = SkillItem.create("art.indefinite", "b1.grammar.articles", "q1", NOW)
    assert item.skill == "art.indefinite"
    assert item.module_id == "b1.grammar.articles"
    assert item.source_item_id == "q1"
    assert item.fsrs.due == NOW
    assert item.fsrs.state == 0
    assert item.fsrs.lapses == 0
    assert item.id is None
    assert not item.is_leech


def test_is_leech_threshold():
    assert LEECH_LAPSES == 4
    under = SkillItem(
        skill="art.definite",
        module_id="b1.grammar.articles",
        source_item_id="q2",
        fsrs=FsrsState(due=NOW, lapses=LEECH_LAPSES - 1),
    )
    exactly = SkillItem(
        skill="art.definite",
        module_id="b1.grammar.articles",
        source_item_id="q2",
        fsrs=FsrsState(due=NOW, lapses=LEECH_LAPSES),
    )
    assert not under.is_leech
    assert exactly.is_leech


def test_with_fsrs_replaces_state_keeping_identity():
    item = SkillItem.create("art.indefinite", "b1.grammar.articles", "q1", NOW)
    updated = item.with_fsrs(FsrsState(due=NOW, state=2, lapses=1))
    assert updated.fsrs.state == 2
    assert updated.fsrs.lapses == 1
    assert updated.skill == item.skill
    assert updated is not item