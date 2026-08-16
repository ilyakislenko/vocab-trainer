from typing import Protocol

from vocab_api.domain.practice.interview import InterviewQuestion


class QuestionBank(Protocol):
    """Source of interview questions.

    `next` must be deterministic so the same topic + used ids always yield the
    same next question, and both must never return a question that has already
    been used (so a session never repeats itself).
    """

    def next(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion: ...
    def random(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion: ...
