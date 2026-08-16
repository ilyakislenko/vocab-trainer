from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ParsedRow:
    word: str
    translation: str
    transcription: str | None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class RowError:
    line: int
    raw: str
    reason: str


Format = Literal["csv", "markdown"]


def _split(line: str, fmt: Format) -> list[str]:
    sep = "," if fmt == "csv" else "|"
    cells = [c.strip() for c in line.split(sep)]
    if fmt == "markdown":
        # Tables written with surrounding pipes add empty edge cells; drop those
        # but keep inner empties so `word | | translation | example` (no IPA) works.
        while cells and cells[0] == "":
            cells.pop(0)
        while cells and cells[-1] == "":
            cells.pop()
    return cells


def _is_markdown_separator(cells: list[str]) -> bool:
    return all(set(c) <= {"-", ":"} and c for c in cells)


def parse_words(raw: str, fmt: Format) -> tuple[list[ParsedRow], list[RowError]]:
    rows: list[ParsedRow] = []
    errors: list[RowError] = []
    seen_header = False
    for index, line in enumerate(raw.splitlines(), start=1):  # 1-based line numbers
        if not line.strip():
            continue
        cells = _split(line, fmt)
        if fmt == "markdown" and _is_markdown_separator(cells):
            seen_header = True
            continue
        if fmt == "markdown" and not seen_header and rows == [] and _looks_like_header(cells):
            continue
        word = cells[0] if cells else ""
        if len(cells) >= 4:
            transcription = cells[1] or None
            translation = cells[2]
            notes = cells[3] or None
        elif len(cells) == 3:
            transcription = cells[1] or None
            translation = cells[2]
            notes = None
        elif len(cells) == 2:
            transcription = None
            translation = cells[1]
            notes = None
        else:
            transcription = None
            translation = ""
            notes = None
        if not word:
            errors.append(RowError(line=index, raw=line, reason="empty word"))
            continue
        if not translation:
            errors.append(RowError(line=index, raw=line, reason="empty translation"))
            continue
        rows.append(
            ParsedRow(word=word, translation=translation, transcription=transcription, notes=notes)
        )
    return rows, errors


def _looks_like_header(cells: list[str]) -> bool:
    lowered = [c.lower() for c in cells]
    return "word" in lowered
