from dataclasses import dataclass
from enum import StrEnum


class Verdict(StrEnum):
    OK = "ok"
    NEEDS_WORK = "needs_work"


@dataclass(frozen=True, slots=True)
class Feedback:
    verdict: Verdict
    feedback: str
    corrected: str | None = None
    example: str | None = None
