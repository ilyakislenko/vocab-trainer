from vocab_api.domain.practice.interview import InterviewQuestion
from vocab_api.infrastructure.question_bank import JsonQuestionBank


def _question(qid: int, topics: tuple[str, ...]) -> InterviewQuestion:
    return InterviewQuestion(
        id=qid, topics=topics, level="Middle", ru=f"Вопрос {qid}", en=f"Question {qid}"
    )


def test_next_picks_lowest_id_matching_topic():
    bank = JsonQuestionBank(
        [
            _question(1, ("Frontend",)),
            _question(2, ("React",)),
            _question(3, ("Frontend", "React")),
        ]
    )
    assert bank.next("React", set()).id == 2
    assert bank.next("Frontend", set()).id == 1


def test_next_skips_used_question_ids():
    bank = JsonQuestionBank(
        [_question(1, ("React",)), _question(2, ("React",)), _question(3, ("React",))]
    )
    assert bank.next("React", {1}).id == 2
    assert bank.next("React", {1, 2}).id == 3


def test_next_falls_back_when_all_matching_are_used():
    bank = JsonQuestionBank([_question(1, ("React",)), _question(2, ("React",))])
    assert bank.next("React", {1, 2}).id == 1


def test_next_unknown_topic_raises():
    bank = JsonQuestionBank([_question(1, ("React",))])
    try:
        bank.next("Unknown", set())
    except ValueError as exc:
        assert "Unknown" in str(exc)
    else:
        raise AssertionError("expected ValueError for unknown topic")
