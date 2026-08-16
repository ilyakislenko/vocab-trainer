from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordHint:
    meaning: str
    example: str | None = None
