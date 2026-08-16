import json
import random
from collections.abc import Sequence
from importlib.resources import files

from vocab_api.application.ports.question_bank import QuestionBank
from vocab_api.domain.practice.interview import InterviewQuestion


class JsonQuestionBank(QuestionBank):
    """Interview questions loaded from the bundled seed JSON.

    `next` is deterministic: the lowest-id question matching the topic and not
    yet used. `random` picks an unused question uniformly. If every matching
    question has been used both fall back to a matching question so a long
    session never gets stuck.
    """

    def __init__(self, questions: Sequence[InterviewQuestion]) -> None:
        self._questions = list(questions)

    def _pool(self, topic: str, used_question_ids: set[int]) -> list[InterviewQuestion]:
        matching = [q for q in self._questions if topic in q.topics]
        if not matching:
            raise ValueError(f"No interview questions for topic {topic!r}")
        unused = [q for q in matching if q.id not in used_question_ids]
        return unused or matching

    def next(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion:
        return min(self._pool(topic, used_question_ids), key=lambda q: q.id)

    def random(self, topic: str, used_question_ids: set[int]) -> InterviewQuestion:
        return random.choice(self._pool(topic, used_question_ids))


def load_interview_questions() -> list[InterviewQuestion]:
    package = files("vocab_api.seed").joinpath("data", "interview-questions.json")
    data = json.loads(package.read_text(encoding="utf-8"))
    return [
        InterviewQuestion(
            id=int(item["id"]),
            topics=tuple(item["topics"]),
            level=str(item["level"]),
            ru=str(item["ru"]),
            en=str(item["en"]),
        )
        for item in data
    ]
