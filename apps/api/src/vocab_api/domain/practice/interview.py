from dataclasses import dataclass

from vocab_api.domain.practice.feedback import Verdict


@dataclass(frozen=True, slots=True)
class InterviewQuestion:
    """A single question from the interview question bank.

    Carries both languages so the client can switch RU/EN without a new
    request; `topics` is the set of interview topics the question belongs to.
    """

    id: int
    topics: tuple[str, ...]
    level: str
    ru: str
    en: str


@dataclass(frozen=True, slots=True)
class InterviewEvaluation:
    """The LLM's verdict on one candidate answer plus how the chat continues.

    The LLM may keep the discussion going with a follow-up `next_question` in
    the interview language, or set `advance` when the candidate asked to move
    on (or the topic is exhausted) so the bank picks the next question.
    """

    verdict: Verdict | None
    feedback: str | None
    corrected: str | None
    advance: bool = False
    next_question: str | None = None


@dataclass(frozen=True, slots=True)
class InterviewTurn:
    """One step of an interview chat.

    `question` is either the bank-picked question (`question_id` set) or an
    LLM follow-up the candidate can answer without consuming a bank question
    (`question_id` None). The client reports a non-null `question_id` back as
    used so questions do not repeat. For the opening question
    `verdict`/`feedback`/`corrected` are None (there is nothing to evaluate).
    """

    verdict: Verdict | None
    feedback: str | None
    corrected: str | None
    question: str
    question_id: int | None
