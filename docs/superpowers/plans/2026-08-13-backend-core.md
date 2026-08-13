# Vocab Trainer — Plan 1: Backend Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable, fully-tested FastAPI backend where you can create a deck, import words, get a spaced-repetition review queue, and record reviews.

**Architecture:** Hexagonal (Ports & Adapters) + DDD. A framework-free `domain/`, an `application/` layer of use cases that depend only on ports (interfaces), and driven/driving adapters in `infrastructure/`/`interfaces/`. Wiring lives only in the composition root (`config/`). SRS scheduling is delegated to `py-fsrs` behind a `Scheduler` port; persistence to SQLite (async SQLModel) behind repository ports.

**Tech Stack:** Python 3.12, uv, FastAPI, Uvicorn, SQLModel + SQLAlchemy async + aiosqlite, py-fsrs, Pydantic v2, pytest + httpx `AsyncClient`, Ruff, mypy (strict), import-linter.

## Global Constraints

- **Python** `>=3.12`. Package/venv manager: **uv**.
- **Architecture is law** (see `CONTRIBUTING.md`): `domain/` imports no framework/IO libs and nothing from `application/`/`infrastructure/`/`interfaces/`; `application/` depends only on `domain/` and its own ports; adapters are wired only in `config/`. Enforced by import-linter (Task 13).
- **Types:** mypy `--strict`; no bare `Any`; no `# type: ignore` without a one-line reason.
- **Quality:** no `TODO`/stub/`pass`-body/`NotImplementedError`/fake returns in committed code. YAGNI.
- **Tests:** every use case unit-tested with in-memory fake adapters (no IO). Never mark a step done without running its command and seeing the stated result.
- **Datetimes:** always timezone-aware UTC (`datetime.now(timezone.utc)`); py-fsrs raises on naive/non-UTC datetimes.
- **Commits:** Conventional Commits; no assistant/tool attribution.
- **Package root:** all backend source under `apps/api/src/vocab_api/`; tests under `apps/api/tests/`. Run commands from `apps/api/`.

---

## File Structure

```
apps/api/
  pyproject.toml                      # deps, ruff, mypy, pytest config
  .importlinter                       # architecture contracts (Task 13)
  .env.example
  src/vocab_api/
    main.py                           # ASGI app (app factory) + healthz
    config/
      settings.py                     # env-backed Settings
      container.py                    # composition root: builds adapters + use cases
    domain/
      shared/errors.py                # DomainError hierarchy
      card/rating.py                  # Rating value object
      card/fsrs_state.py              # FsrsState value object
      card/card.py                    # Card aggregate
      deck/deck.py                    # Deck aggregate
      review/review_log.py            # ReviewLogEntry
    application/
      ports/clock.py                  # Clock protocol
      ports/scheduler.py              # Scheduler protocol
      ports/repositories.py           # DeckRepository, CardRepository, ReviewLogRepository
      importing/parser.py             # parse_words + ParsedRow/RowError
      use_cases/decks.py              # CreateDeck, ListDecks
      use_cases/importing.py          # ImportWords + ImportResult
      use_cases/review.py             # GetReviewQueue, RecordReview
      use_cases/stats.py              # GetStats + Stats
    infrastructure/
      clock.py                        # SystemClock
      scheduling/py_fsrs_scheduler.py # PyFsrsScheduler (Scheduler adapter)
      persistence/tables.py           # SQLModel rows: DeckRow, CardRow, ReviewLogRow
      persistence/engine.py           # async engine + session factory + init_db
      persistence/mappers.py          # domain <-> row mapping
      persistence/deck_repo.py        # SqlDeckRepository
      persistence/card_repo.py        # SqlCardRepository
      persistence/review_log_repo.py  # SqlReviewLogRepository
    interfaces/http/
      errors.py                       # domain error -> HTTP mapping
      dto.py                          # Pydantic request/response models
      deps.py                         # FastAPI dependency providers (pull from container)
      decks_router.py
      review_router.py
      stats_router.py
  tests/
    conftest.py                       # fakes + fixtures
    domain/ application/ infrastructure/ http/   # mirror src
.github/workflows/ci.yml
```

---

### Task 1: Project scaffold, tooling, and `/healthz`

**Files:**
- Create: `apps/api/pyproject.toml`, `apps/api/src/vocab_api/__init__.py`, `apps/api/src/vocab_api/main.py`, `apps/api/tests/__init__.py`, `apps/api/tests/http/test_healthz.py`, `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `create_app() -> fastapi.FastAPI` in `main.py`; `GET /healthz` → `{"status": "ok"}`.

- [ ] **Step 1: Initialize the uv project and dependencies**

Run from repo root:
```bash
cd apps/api
uv init --package --name vocab-api --python 3.12 .
uv add fastapi "uvicorn[standard]" sqlmodel aiosqlite "pydantic-settings" "fsrs>=5,<6"
uv add --dev pytest pytest-asyncio httpx ruff mypy import-linter
```

- [ ] **Step 2: Configure tooling in `pyproject.toml`**

Append:
```toml
[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ASYNC", "RUF"]

[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = "src"
packages = ["vocab_api"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 3: Write the failing test**

`tests/http/test_healthz.py`:
```python
import httpx
import pytest
from vocab_api.main import create_app


@pytest.mark.asyncio
async def test_healthz_returns_ok():
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `uv run pytest tests/http/test_healthz.py -v`
Expected: FAIL — `ImportError` / `create_app` not found.

- [ ] **Step 5: Implement `create_app` and the healthz route**

`src/vocab_api/main.py`:
```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Vocab Trainer API")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Run tests, lint, and types — all must pass**

Run:
```bash
uv run pytest -q
uv run ruff check .
uv run mypy
```
Expected: pytest PASS; ruff clean; mypy `Success`.

- [ ] **Step 7: Add CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: ci
on: [push, pull_request]
jobs:
  api:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/api
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run mypy
      - run: uv run pytest -q
      - run: uv run lint-imports
```

- [ ] **Step 8: Commit**

```bash
git add apps/api .github
git commit -m "feat(api): scaffold FastAPI app with tooling and healthz"
```

---

### Task 2: Domain value objects — `Rating` and `FsrsState`

**Files:**
- Create: `src/vocab_api/domain/__init__.py`, `src/vocab_api/domain/card/__init__.py`, `src/vocab_api/domain/card/rating.py`, `src/vocab_api/domain/card/fsrs_state.py`, `tests/domain/test_fsrs_state.py`

**Interfaces:**
- Produces:
  - `Rating(IntEnum)` with `AGAIN=1, HARD=2, GOOD=3, EASY=4`.
  - `FsrsState` frozen dataclass: `due: datetime`, `state: int = 1`, `step: int | None = 0`, `stability: float | None = None`, `difficulty: float | None = None`, `last_review: datetime | None = None`; staticmethod `FsrsState.new(now: datetime) -> FsrsState`.

- [ ] **Step 1: Write the failing test**

`tests/domain/test_fsrs_state.py`:
```python
from datetime import datetime, timezone

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating


def test_new_state_is_due_now_and_learning():
    now = datetime(2026, 8, 13, tzinfo=timezone.utc)
    state = FsrsState.new(now)
    assert state.due == now
    assert state.state == 1
    assert state.step == 0
    assert state.stability is None
    assert state.last_review is None


def test_ratings_map_to_fsrs_values():
    assert (Rating.AGAIN, Rating.HARD, Rating.GOOD, Rating.EASY) == (1, 2, 3, 4)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/domain/test_fsrs_state.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the value objects**

`src/vocab_api/domain/card/rating.py`:
```python
from enum import IntEnum


class Rating(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4
```

`src/vocab_api/domain/card/fsrs_state.py`:
```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FsrsState:
    due: datetime
    state: int = 1  # 1=Learning, 2=Review, 3=Relearning
    step: int | None = 0
    stability: float | None = None
    difficulty: float | None = None
    last_review: datetime | None = None

    @staticmethod
    def new(now: datetime) -> "FsrsState":
        return FsrsState(due=now)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/domain/test_fsrs_state.py -v` → PASS. Then `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/domain tests/domain
git commit -m "feat(domain): add Rating and FsrsState value objects"
```

---

### Task 3: Domain aggregates — `Deck`, `Card`, and errors

**Files:**
- Create: `src/vocab_api/domain/shared/__init__.py`, `src/vocab_api/domain/shared/errors.py`, `src/vocab_api/domain/deck/__init__.py`, `src/vocab_api/domain/deck/deck.py`, `src/vocab_api/domain/card/card.py`, `tests/domain/test_deck.py`, `tests/domain/test_card.py`

**Interfaces:**
- Produces:
  - Errors: `DomainError`, `EmptyDeckName`, `EmptyWord`, `EmptyTranslation`, `DeckNotFound(deck_id: int)`, `CardNotFound(card_id: int)`.
  - `Deck` frozen dataclass: `name: str`, `id: int | None = None`, `created_at: datetime | None = None`; `Deck.create(name: str, now: datetime) -> Deck`.
  - `Card` frozen dataclass: `deck_id: int`, `word: str`, `translation: str`, `fsrs: FsrsState`, `transcription: str | None = None`, `notes: str | None = None`, `id: int | None = None`, `created_at: datetime | None = None`; `Card.create(deck_id, word, translation, now, transcription=None, notes=None) -> Card`; `card.with_fsrs(fsrs: FsrsState) -> Card`.

- [ ] **Step 1: Write the failing tests**

`tests/domain/test_deck.py`:
```python
from datetime import datetime, timezone

import pytest

from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import EmptyDeckName

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)


def test_create_trims_and_sets_created_at():
    deck = Deck.create("  Travel  ", NOW)
    assert deck.name == "Travel"
    assert deck.created_at == NOW
    assert deck.id is None


def test_blank_name_rejected():
    with pytest.raises(EmptyDeckName):
        Deck.create("   ", NOW)
```

`tests/domain/test_card.py`:
```python
from datetime import datetime, timezone

import pytest

from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.shared.errors import EmptyTranslation, EmptyWord

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)


def test_create_builds_due_now_card():
    card = Card.create(deck_id=1, word=" run ", translation=" бежать ", now=NOW)
    assert card.word == "run"
    assert card.translation == "бежать"
    assert card.fsrs == FsrsState.new(NOW)
    assert card.deck_id == 1


def test_blank_word_or_translation_rejected():
    with pytest.raises(EmptyWord):
        Card.create(deck_id=1, word="", translation="x", now=NOW)
    with pytest.raises(EmptyTranslation):
        Card.create(deck_id=1, word="x", translation=" ", now=NOW)


def test_with_fsrs_returns_updated_copy():
    card = Card.create(deck_id=1, word="run", translation="бежать", now=NOW)
    later = FsrsState(due=NOW, state=2, stability=5.0)
    updated = card.with_fsrs(later)
    assert updated.fsrs == later
    assert card.fsrs != later  # original unchanged
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/domain/test_deck.py tests/domain/test_card.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement errors and aggregates**

`src/vocab_api/domain/shared/errors.py`:
```python
class DomainError(Exception):
    """Base class for domain rule violations."""


class EmptyDeckName(DomainError):
    pass


class EmptyWord(DomainError):
    pass


class EmptyTranslation(DomainError):
    pass


class DeckNotFound(DomainError):
    def __init__(self, deck_id: int) -> None:
        super().__init__(f"deck {deck_id} not found")
        self.deck_id = deck_id


class CardNotFound(DomainError):
    def __init__(self, card_id: int) -> None:
        super().__init__(f"card {card_id} not found")
        self.card_id = card_id
```

`src/vocab_api/domain/deck/deck.py`:
```python
from dataclasses import dataclass
from datetime import datetime

from vocab_api.domain.shared.errors import EmptyDeckName


@dataclass(frozen=True, slots=True)
class Deck:
    name: str
    id: int | None = None
    created_at: datetime | None = None

    @staticmethod
    def create(name: str, now: datetime) -> "Deck":
        cleaned = name.strip()
        if not cleaned:
            raise EmptyDeckName()
        return Deck(name=cleaned, created_at=now)
```

`src/vocab_api/domain/card/card.py`:
```python
from dataclasses import dataclass, replace
from datetime import datetime

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.shared.errors import EmptyTranslation, EmptyWord


@dataclass(frozen=True, slots=True)
class Card:
    deck_id: int
    word: str
    translation: str
    fsrs: FsrsState
    transcription: str | None = None
    notes: str | None = None
    id: int | None = None
    created_at: datetime | None = None

    @staticmethod
    def create(
        deck_id: int,
        word: str,
        translation: str,
        now: datetime,
        transcription: str | None = None,
        notes: str | None = None,
    ) -> "Card":
        clean_word = word.strip()
        if not clean_word:
            raise EmptyWord()
        clean_translation = translation.strip()
        if not clean_translation:
            raise EmptyTranslation()
        return Card(
            deck_id=deck_id,
            word=clean_word,
            translation=clean_translation,
            transcription=(transcription or None) and transcription.strip() or None,
            notes=(notes or None) and notes.strip() or None,
            fsrs=FsrsState.new(now),
            created_at=now,
        )

    def with_fsrs(self, fsrs: FsrsState) -> "Card":
        return replace(self, fsrs=fsrs)
```

- [ ] **Step 4: Run the tests and mypy**

Run: `uv run pytest tests/domain -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/domain tests/domain
git commit -m "feat(domain): add Deck and Card aggregates with errors"
```

---

### Task 4: Import parser — `parse_words`

**Files:**
- Create: `src/vocab_api/application/__init__.py`, `src/vocab_api/application/importing/__init__.py`, `src/vocab_api/application/importing/parser.py`, `tests/application/test_parser.py`

**Interfaces:**
- Produces:
  - `ParsedRow` frozen dataclass: `word: str`, `translation: str`, `transcription: str | None`.
  - `RowError` frozen dataclass: `line: int`, `raw: str`, `reason: str`.
  - `parse_words(raw: str, fmt: Literal["csv", "markdown"]) -> tuple[list[ParsedRow], list[RowError]]`.
- Rules: `csv` splits on commas, columns `word,transcription,translation` (transcription optional if 2 columns → treated as `word,translation`); `markdown` parses pipe tables, skipping the header separator row (`|---|`). Blank lines skipped. A row with an empty word or empty translation becomes a `RowError`; other rows still parse.

- [ ] **Step 1: Write the failing test**

`tests/application/test_parser.py`:
```python
from vocab_api.application.importing.parser import ParsedRow, RowError, parse_words


def test_csv_three_columns():
    rows, errors = parse_words("run,rʌn,бежать\njump,dʒʌmp,прыгать", "csv")
    assert errors == []
    assert rows == [
        ParsedRow(word="run", translation="бежать", transcription="rʌn"),
        ParsedRow(word="jump", translation="прыгать", transcription="dʒʌmp"),
    ]


def test_csv_two_columns_has_no_transcription():
    rows, errors = parse_words("run,бежать", "csv")
    assert rows == [ParsedRow(word="run", translation="бежать", transcription=None)]
    assert errors == []


def test_markdown_table_skips_header_and_separator():
    md = "| word | ipa | translation |\n|---|---|---|\n| run | rʌn | бежать |"
    rows, errors = parse_words(md, "markdown")
    assert rows == [ParsedRow(word="run", translation="бежать", transcription="rʌn")]
    assert errors == []


def test_row_missing_word_is_reported_but_others_parse():
    rows, errors = parse_words(",ipa,бежать\njump,dʒʌmp,прыгать", "csv")
    assert rows == [ParsedRow(word="jump", translation="прыгать", transcription="dʒʌmp")]
    assert errors == [RowError(line=1, raw=",ipa,бежать", reason="empty word")]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/application/test_parser.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the parser**

`src/vocab_api/application/importing/parser.py`:
```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ParsedRow:
    word: str
    translation: str
    transcription: str | None


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
        cells = [c for c in cells if c != ""] or [""]
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
        if len(cells) >= 3:
            transcription: str | None = cells[1] or None
            translation = cells[2]
        elif len(cells) == 2:
            transcription = None
            translation = cells[1]
        else:
            transcription = None
            translation = ""
        if not word:
            errors.append(RowError(line=index, raw=line, reason="empty word"))
            continue
        if not translation:
            errors.append(RowError(line=index, raw=line, reason="empty translation"))
            continue
        rows.append(ParsedRow(word=word, translation=translation, transcription=transcription))
    return rows, errors


def _looks_like_header(cells: list[str]) -> bool:
    lowered = [c.lower() for c in cells]
    return "word" in lowered
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/application/test_parser.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/application/importing tests/application/test_parser.py
git commit -m "feat(application): add CSV/markdown word-list parser"
```

---

### Task 5: Ports + `SystemClock`

**Files:**
- Create: `src/vocab_api/application/ports/__init__.py`, `src/vocab_api/application/ports/clock.py`, `src/vocab_api/application/ports/scheduler.py`, `src/vocab_api/application/ports/repositories.py`, `src/vocab_api/domain/review/__init__.py`, `src/vocab_api/domain/review/review_log.py`, `src/vocab_api/infrastructure/__init__.py`, `src/vocab_api/infrastructure/clock.py`, `tests/infrastructure/test_clock.py`

**Interfaces:**
- Produces:
  - `ReviewLogEntry` frozen dataclass: `card_id: int`, `rating: Rating`, `reviewed_at: datetime`.
  - `Clock(Protocol)`: `def now(self) -> datetime`.
  - `Scheduler(Protocol)`: `def review(self, state: FsrsState, rating: Rating, now: datetime) -> FsrsState`.
  - `DeckRepository(Protocol)`: `async add(deck) -> Deck`, `async get(deck_id) -> Deck`, `async list() -> list[Deck]`.
  - `CardRepository(Protocol)`: `async add_many(cards) -> list[Card]`, `async get(card_id) -> Card`, `async save(card) -> None`, `async due(deck_id, now, limit) -> list[Card]`, `async count_due(deck_id, now) -> int`.
  - `ReviewLogRepository(Protocol)`: `async add(entry) -> None`, `async count_reviews(deck_id) -> int`.
  - `SystemClock` implementing `Clock`, returning tz-aware UTC.

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_clock.py`:
```python
from datetime import timezone

from vocab_api.infrastructure.clock import SystemClock


def test_system_clock_returns_utc_aware():
    now = SystemClock().now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timezone.utc.utcoffset(now)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/infrastructure/test_clock.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Define ports and the ReviewLogEntry, implement SystemClock**

`src/vocab_api/domain/review/review_log.py`:
```python
from dataclasses import dataclass
from datetime import datetime

from vocab_api.domain.card.rating import Rating


@dataclass(frozen=True, slots=True)
class ReviewLogEntry:
    card_id: int
    rating: Rating
    reviewed_at: datetime
```

`src/vocab_api/application/ports/clock.py`:
```python
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...
```

`src/vocab_api/application/ports/scheduler.py`:
```python
from datetime import datetime
from typing import Protocol

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating


class Scheduler(Protocol):
    def review(self, state: FsrsState, rating: Rating, now: datetime) -> FsrsState: ...
```

`src/vocab_api/application/ports/repositories.py`:
```python
from datetime import datetime
from typing import Protocol

from vocab_api.domain.card.card import Card
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.review.review_log import ReviewLogEntry


class DeckRepository(Protocol):
    async def add(self, deck: Deck) -> Deck: ...
    async def get(self, deck_id: int) -> Deck: ...
    async def list(self) -> list[Deck]: ...


class CardRepository(Protocol):
    async def add_many(self, cards: list[Card]) -> list[Card]: ...
    async def get(self, card_id: int) -> Card: ...
    async def save(self, card: Card) -> None: ...
    async def due(self, deck_id: int, now: datetime, limit: int) -> list[Card]: ...
    async def count_due(self, deck_id: int, now: datetime) -> int: ...


class ReviewLogRepository(Protocol):
    async def add(self, entry: ReviewLogEntry) -> None: ...
    async def count_reviews(self, deck_id: int) -> int: ...
```

`src/vocab_api/infrastructure/clock.py`:
```python
from datetime import datetime, timezone

from vocab_api.application.ports.clock import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

- [ ] **Step 4: Run the test and mypy**

Run: `uv run pytest tests/infrastructure/test_clock.py -v` → PASS; `uv run mypy` → Success (confirms `SystemClock` satisfies `Clock`).

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/application/ports src/vocab_api/domain/review src/vocab_api/infrastructure/clock.py tests/infrastructure/test_clock.py
git commit -m "feat(application): define ports and SystemClock"
```

---

### Task 6: Scheduler adapter — `PyFsrsScheduler`

**Files:**
- Create: `src/vocab_api/infrastructure/scheduling/__init__.py`, `src/vocab_api/infrastructure/scheduling/py_fsrs_scheduler.py`, `tests/infrastructure/test_py_fsrs_scheduler.py`

**Interfaces:**
- Consumes: `FsrsState`, `Rating`, `Scheduler` port.
- Produces: `PyFsrsScheduler` implementing `Scheduler`; maps `FsrsState` to/from a py-fsrs `Card` via its documented `to_dict()`/`from_dict()`.

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_py_fsrs_scheduler.py`:
```python
from datetime import datetime, timezone

from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.infrastructure.scheduling.py_fsrs_scheduler import PyFsrsScheduler

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


def test_reviewing_new_card_pushes_due_into_the_future_and_records_stability():
    scheduler = PyFsrsScheduler()
    new_state = FsrsState.new(NOW)
    updated = scheduler.review(new_state, Rating.GOOD, NOW)
    assert updated.due > NOW
    assert updated.stability is not None
    assert updated.last_review == NOW


def test_again_schedules_sooner_than_easy():
    scheduler = PyFsrsScheduler()
    again = scheduler.review(FsrsState.new(NOW), Rating.AGAIN, NOW)
    easy = scheduler.review(FsrsState.new(NOW), Rating.EASY, NOW)
    assert again.due < easy.due
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/infrastructure/test_py_fsrs_scheduler.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the adapter**

`src/vocab_api/infrastructure/scheduling/py_fsrs_scheduler.py`:
```python
from datetime import datetime

from fsrs import Card as FsrsCard
from fsrs import Rating as FsrsRating
from fsrs import Scheduler as _FsrsScheduler

from vocab_api.application.ports.scheduler import Scheduler
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating


class PyFsrsScheduler(Scheduler):
    def __init__(self) -> None:
        self._scheduler = _FsrsScheduler(enable_fuzzing=False)

    def review(self, state: FsrsState, rating: Rating, now: datetime) -> FsrsState:
        card = FsrsCard.from_dict(self._to_dict(state))
        updated, _log = self._scheduler.review_card(
            card=card, rating=FsrsRating(rating.value), review_datetime=now
        )
        return self._from_dict(updated.to_dict())

    @staticmethod
    def _to_dict(state: FsrsState) -> dict[str, object]:
        return {
            "card_id": 1,
            "state": state.state,
            "step": state.step,
            "stability": state.stability,
            "difficulty": state.difficulty,
            "due": state.due.isoformat(),
            "last_review": state.last_review.isoformat() if state.last_review else None,
        }

    @staticmethod
    def _from_dict(data: dict[str, object]) -> FsrsState:
        last = data["last_review"]
        return FsrsState(
            due=datetime.fromisoformat(str(data["due"])),
            state=int(data["state"]),  # type: ignore[arg-type]  # CardDict.state is int
            step=data["step"],  # type: ignore[arg-type]
            stability=data["stability"],  # type: ignore[arg-type]
            difficulty=data["difficulty"],  # type: ignore[arg-type]
            last_review=datetime.fromisoformat(str(last)) if last else None,
        )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/infrastructure/test_py_fsrs_scheduler.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/infrastructure/scheduling tests/infrastructure/test_py_fsrs_scheduler.py
git commit -m "feat(infra): add py-fsrs scheduler adapter"
```

---

### Task 7: Persistence tables + async engine

**Files:**
- Create: `src/vocab_api/infrastructure/persistence/__init__.py`, `src/vocab_api/infrastructure/persistence/tables.py`, `src/vocab_api/infrastructure/persistence/engine.py`, `tests/infrastructure/test_engine.py`

**Interfaces:**
- Produces:
  - SQLModel tables (`table=True`): `DeckRow(id, name, created_at)`; `CardRow(id, deck_id, word, translation, transcription, notes, created_at, fsrs_state, fsrs_step, fsrs_stability, fsrs_difficulty, fsrs_due, fsrs_last_review)`; `ReviewLogRow(id, card_id, rating, reviewed_at)`. `CardRow` has indexes on `deck_id` and `fsrs_due`.
  - `Database(url: str)` with `async init(self) -> None` (create tables) and `def session(self) -> AsyncSession` (async context manager via `async_sessionmaker`).

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_engine.py`:
```python
from sqlmodel import select

from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.tables import DeckRow


async def test_init_creates_tables_and_roundtrips_a_row():
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    async with db.session() as session:
        session.add(DeckRow(name="Travel"))
        await session.commit()
    async with db.session() as session:
        result = await session.execute(select(DeckRow))
        decks = result.scalars().all()
    assert [d.name for d in decks] == ["Travel"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/infrastructure/test_engine.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement tables and engine**

`src/vocab_api/infrastructure/persistence/tables.py`:
```python
from datetime import datetime

from sqlmodel import Field, SQLModel


class DeckRow(SQLModel, table=True):
    __tablename__ = "decks"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime | None = None


class CardRow(SQLModel, table=True):
    __tablename__ = "cards"
    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(index=True, foreign_key="decks.id")
    word: str
    translation: str
    transcription: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    fsrs_state: int = 1
    fsrs_step: int | None = 0
    fsrs_stability: float | None = None
    fsrs_difficulty: float | None = None
    fsrs_due: datetime = Field(index=True)
    fsrs_last_review: datetime | None = None


class ReviewLogRow(SQLModel, table=True):
    __tablename__ = "review_logs"
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(index=True, foreign_key="cards.id")
    rating: int
    reviewed_at: datetime
```

`src/vocab_api/infrastructure/persistence/engine.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from vocab_api.infrastructure.persistence import tables  # noqa: F401  # register metadata


class Database:
    def __init__(self, url: str) -> None:
        # In-memory SQLite gives each new connection its own empty database, which
        # breaks repositories that open a session per call. StaticPool pins a single
        # shared connection so the schema and data persist across sessions.
        # All app datetimes are UTC; SQLite stores them naive-UTC, so comparisons
        # (fsrs_due <= now) stay consistent.
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {}
        if "memory" in url:
            connect_args["check_same_thread"] = False
            engine_kwargs["poolclass"] = StaticPool
        self._engine = create_async_engine(url, connect_args=connect_args, **engine_kwargs)
        self._session_factory = async_sessionmaker(self._engine, class_=AsyncSession)

    async def init(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    def session(self) -> AsyncSession:
        return self._session_factory()
```

- [ ] **Step 4: Run the test and mypy**

Run: `uv run pytest tests/infrastructure/test_engine.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/infrastructure/persistence tests/infrastructure/test_engine.py
git commit -m "feat(infra): add SQLModel tables and async database engine"
```

---

### Task 8: `SqlDeckRepository` + mappers

**Files:**
- Create: `src/vocab_api/infrastructure/persistence/mappers.py`, `src/vocab_api/infrastructure/persistence/deck_repo.py`, `tests/infrastructure/test_deck_repo.py`

**Interfaces:**
- Consumes: `Database`, `DeckRow`, `Deck`, `DeckRepository`, `DeckNotFound`.
- Produces:
  - `mappers.deck_to_row(deck) -> DeckRow`, `mappers.deck_from_row(row) -> Deck`.
  - `SqlDeckRepository(db: Database)` implementing `DeckRepository`.

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_deck_repo.py`:
```python
from datetime import datetime, timezone

import pytest

from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import DeckNotFound
from vocab_api.infrastructure.persistence.deck_repo import SqlDeckRepository
from vocab_api.infrastructure.persistence.engine import Database

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)


async def _repo() -> SqlDeckRepository:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    return SqlDeckRepository(db)


async def test_add_assigns_id_and_get_returns_it():
    repo = await _repo()
    saved = await repo.add(Deck.create("Travel", NOW))
    assert saved.id is not None
    fetched = await repo.get(saved.id)
    assert fetched.name == "Travel"


async def test_get_missing_raises():
    repo = await _repo()
    with pytest.raises(DeckNotFound):
        await repo.get(999)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/infrastructure/test_deck_repo.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement mappers and repository**

`src/vocab_api/infrastructure/persistence/mappers.py`:
```python
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.deck.deck import Deck
from vocab_api.infrastructure.persistence.tables import CardRow, DeckRow


def deck_to_row(deck: Deck) -> DeckRow:
    return DeckRow(id=deck.id, name=deck.name, created_at=deck.created_at)


def deck_from_row(row: DeckRow) -> Deck:
    return Deck(id=row.id, name=row.name, created_at=row.created_at)


def card_to_row(card: Card) -> CardRow:
    return CardRow(
        id=card.id,
        deck_id=card.deck_id,
        word=card.word,
        translation=card.translation,
        transcription=card.transcription,
        notes=card.notes,
        created_at=card.created_at,
        fsrs_state=card.fsrs.state,
        fsrs_step=card.fsrs.step,
        fsrs_stability=card.fsrs.stability,
        fsrs_difficulty=card.fsrs.difficulty,
        fsrs_due=card.fsrs.due,
        fsrs_last_review=card.fsrs.last_review,
    )


def card_from_row(row: CardRow) -> Card:
    return Card(
        id=row.id,
        deck_id=row.deck_id,
        word=row.word,
        translation=row.translation,
        transcription=row.transcription,
        notes=row.notes,
        created_at=row.created_at,
        fsrs=FsrsState(
            due=row.fsrs_due,
            state=row.fsrs_state,
            step=row.fsrs_step,
            stability=row.fsrs_stability,
            difficulty=row.fsrs_difficulty,
            last_review=row.fsrs_last_review,
        ),
    )
```

`src/vocab_api/infrastructure/persistence/deck_repo.py`:
```python
from sqlmodel import select

from vocab_api.application.ports.repositories import DeckRepository
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.shared.errors import DeckNotFound
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.mappers import deck_from_row, deck_to_row
from vocab_api.infrastructure.persistence.tables import DeckRow


class SqlDeckRepository(DeckRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, deck: Deck) -> Deck:
        row = deck_to_row(deck)
        async with self._db.session() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return deck_from_row(row)

    async def get(self, deck_id: int) -> Deck:
        async with self._db.session() as session:
            row = await session.get(DeckRow, deck_id)
        if row is None:
            raise DeckNotFound(deck_id)
        return deck_from_row(row)

    async def list(self) -> list[Deck]:
        async with self._db.session() as session:
            result = await session.execute(select(DeckRow).order_by(DeckRow.id))
            rows = result.scalars().all()
        return [deck_from_row(row) for row in rows]
```

- [ ] **Step 4: Run the test and mypy**

Run: `uv run pytest tests/infrastructure/test_deck_repo.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/infrastructure/persistence/mappers.py src/vocab_api/infrastructure/persistence/deck_repo.py tests/infrastructure/test_deck_repo.py
git commit -m "feat(infra): add deck repository and domain<->row mappers"
```

---

### Task 9: `SqlCardRepository` + `SqlReviewLogRepository`

**Files:**
- Create: `src/vocab_api/infrastructure/persistence/card_repo.py`, `src/vocab_api/infrastructure/persistence/review_log_repo.py`, `tests/infrastructure/test_card_repo.py`

**Interfaces:**
- Consumes: `Database`, mappers, `CardRow`, `ReviewLogRow`, `Card`, `ReviewLogEntry`, `CardRepository`, `ReviewLogRepository`, `CardNotFound`.
- Produces: `SqlCardRepository(db)` and `SqlReviewLogRepository(db)`. `due()` returns cards with `fsrs_due <= now` ordered by `fsrs_due`, capped at `limit`.

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_card_repo.py`:
```python
from datetime import datetime, timedelta, timezone

import pytest

from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.shared.errors import CardNotFound
from vocab_api.infrastructure.persistence.card_repo import SqlCardRepository
from vocab_api.infrastructure.persistence.review_log_repo import SqlReviewLogRepository
from vocab_api.infrastructure.persistence.engine import Database

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


async def _db() -> Database:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    return db


async def test_add_many_assigns_ids_and_due_filters_and_orders():
    db = await _db()
    repo = SqlCardRepository(db)
    future = Card.create(1, "later", "позже", NOW).with_fsrs(FsrsState(due=NOW + timedelta(days=1)))
    due_now = Card.create(1, "now", "сейчас", NOW)
    saved = await repo.add_many([future, due_now])
    assert all(c.id is not None for c in saved)

    due = await repo.due(deck_id=1, now=NOW, limit=10)
    assert [c.word for c in due] == ["now"]
    assert await repo.count_due(deck_id=1, now=NOW) == 1


async def test_save_persists_updated_fsrs_and_get_missing_raises():
    db = await _db()
    repo = SqlCardRepository(db)
    (card,) = await repo.add_many([Card.create(1, "run", "бежать", NOW)])
    assert card.id is not None
    await repo.save(card.with_fsrs(FsrsState(due=NOW + timedelta(days=3), stability=9.0)))
    reloaded = await repo.get(card.id)
    assert reloaded.fsrs.stability == 9.0
    with pytest.raises(CardNotFound):
        await repo.get(999)


async def test_review_log_add_and_count():
    db = await _db()
    cards = SqlCardRepository(db)
    (card,) = await cards.add_many([Card.create(1, "run", "бежать", NOW)])
    assert card.id is not None
    logs = SqlReviewLogRepository(db)
    await logs.add(ReviewLogEntry(card_id=card.id, rating=Rating.GOOD, reviewed_at=NOW))
    assert await logs.count_reviews(deck_id=1) == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/infrastructure/test_card_repo.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement the repositories**

`src/vocab_api/infrastructure/persistence/card_repo.py`:
```python
from datetime import datetime

from sqlmodel import select

from vocab_api.application.ports.repositories import CardRepository
from vocab_api.domain.card.card import Card
from vocab_api.domain.shared.errors import CardNotFound
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.mappers import card_from_row, card_to_row
from vocab_api.infrastructure.persistence.tables import CardRow


class SqlCardRepository(CardRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add_many(self, cards: list[Card]) -> list[Card]:
        rows = [card_to_row(card) for card in cards]
        async with self._db.session() as session:
            session.add_all(rows)
            await session.commit()
            for row in rows:
                await session.refresh(row)
        return [card_from_row(row) for row in rows]

    async def get(self, card_id: int) -> Card:
        async with self._db.session() as session:
            row = await session.get(CardRow, card_id)
        if row is None:
            raise CardNotFound(card_id)
        return card_from_row(row)

    async def save(self, card: Card) -> None:
        row = card_to_row(card)
        async with self._db.session() as session:
            await session.merge(row)
            await session.commit()

    async def due(self, deck_id: int, now: datetime, limit: int) -> list[Card]:
        statement = (
            select(CardRow)
            .where(CardRow.deck_id == deck_id, CardRow.fsrs_due <= now)
            .order_by(CardRow.fsrs_due)
            .limit(limit)
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [card_from_row(row) for row in rows]

    async def count_due(self, deck_id: int, now: datetime) -> int:
        statement = select(CardRow).where(
            CardRow.deck_id == deck_id, CardRow.fsrs_due <= now
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            return len(result.scalars().all())
```

`src/vocab_api/infrastructure/persistence/review_log_repo.py`:
```python
from sqlmodel import select

from vocab_api.application.ports.repositories import ReviewLogRepository
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.tables import CardRow, ReviewLogRow


class SqlReviewLogRepository(ReviewLogRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, entry: ReviewLogEntry) -> None:
        row = ReviewLogRow(
            card_id=entry.card_id,
            rating=int(entry.rating),
            reviewed_at=entry.reviewed_at,
        )
        async with self._db.session() as session:
            session.add(row)
            await session.commit()

    async def count_reviews(self, deck_id: int) -> int:
        statement = (
            select(ReviewLogRow)
            .join(CardRow, CardRow.id == ReviewLogRow.card_id)
            .where(CardRow.deck_id == deck_id)
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            return len(result.scalars().all())
```

- [ ] **Step 4: Run the test and mypy**

Run: `uv run pytest tests/infrastructure/test_card_repo.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/infrastructure/persistence/card_repo.py src/vocab_api/infrastructure/persistence/review_log_repo.py tests/infrastructure/test_card_repo.py
git commit -m "feat(infra): add card and review-log repositories"
```

---

### Task 10: Use cases — `CreateDeck`, `ListDecks`, `ImportWords` (with fakes)

**Files:**
- Create: `src/vocab_api/application/use_cases/__init__.py`, `src/vocab_api/application/use_cases/decks.py`, `src/vocab_api/application/use_cases/importing.py`, `tests/conftest.py`, `tests/application/test_decks_use_cases.py`, `tests/application/test_import_use_case.py`

**Interfaces:**
- Consumes: `DeckRepository`, `CardRepository`, `Clock` ports; `parse_words`, `Deck`, `Card`.
- Produces:
  - `CreateDeck(deck_repo, clock)`: `async execute(name: str) -> Deck`.
  - `ListDecks(deck_repo)`: `async execute() -> list[Deck]`.
  - `ImportResult` frozen dataclass: `imported: list[Card]`, `errors: list[RowError]`, `committed: bool`.
  - `ImportWords(deck_repo, card_repo, clock)`: `async execute(deck_id: int, raw: str, fmt: Format, dry_run: bool) -> ImportResult`. Verifies the deck exists (raises `DeckNotFound`); parses; on `dry_run=True` returns parsed cards without persisting (`committed=False`); on `dry_run=False` persists via `add_many` and returns saved cards (`committed=True`). Parse errors are always returned; a fully-invalid non-dry-run import commits the valid subset.

- [ ] **Step 1: Write the shared fakes in `conftest.py`**

`tests/conftest.py`:
```python
from datetime import datetime, timezone

from vocab_api.domain.card.card import Card
from vocab_api.domain.deck.deck import Deck
from vocab_api.domain.review.review_log import ReviewLogEntry
from vocab_api.domain.shared.errors import CardNotFound, DeckNotFound

FIXED_NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


class FixedClock:
    def __init__(self, now: datetime = FIXED_NOW) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakeDeckRepository:
    def __init__(self) -> None:
        self._items: dict[int, Deck] = {}
        self._seq = 0

    async def add(self, deck: Deck) -> Deck:
        self._seq += 1
        stored = Deck(id=self._seq, name=deck.name, created_at=deck.created_at)
        self._items[self._seq] = stored
        return stored

    async def get(self, deck_id: int) -> Deck:
        if deck_id not in self._items:
            raise DeckNotFound(deck_id)
        return self._items[deck_id]

    async def list(self) -> list[Deck]:
        return list(self._items.values())


class FakeCardRepository:
    def __init__(self) -> None:
        self._items: dict[int, Card] = {}
        self._seq = 0

    async def add_many(self, cards: list[Card]) -> list[Card]:
        saved: list[Card] = []
        for card in cards:
            self._seq += 1
            stored = Card(
                id=self._seq, deck_id=card.deck_id, word=card.word,
                translation=card.translation, fsrs=card.fsrs,
                transcription=card.transcription, notes=card.notes,
                created_at=card.created_at,
            )
            self._items[self._seq] = stored
            saved.append(stored)
        return saved

    async def get(self, card_id: int) -> Card:
        if card_id not in self._items:
            raise CardNotFound(card_id)
        return self._items[card_id]

    async def save(self, card: Card) -> None:
        assert card.id is not None
        self._items[card.id] = card

    async def due(self, deck_id: int, now: datetime, limit: int) -> list[Card]:
        due = [c for c in self._items.values() if c.deck_id == deck_id and c.fsrs.due <= now]
        due.sort(key=lambda c: c.fsrs.due)
        return due[:limit]

    async def count_due(self, deck_id: int, now: datetime) -> int:
        return len([c for c in self._items.values() if c.deck_id == deck_id and c.fsrs.due <= now])


class FakeReviewLogRepository:
    def __init__(self) -> None:
        self.entries: list[ReviewLogEntry] = []

    async def add(self, entry: ReviewLogEntry) -> None:
        self.entries.append(entry)

    async def count_reviews(self, deck_id: int) -> int:
        return len(self.entries)
```

- [ ] **Step 2: Write the failing use-case tests**

`tests/application/test_decks_use_cases.py`:
```python
import pytest

from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.domain.shared.errors import EmptyDeckName
from tests.conftest import FakeDeckRepository, FixedClock


async def test_create_deck_persists_and_returns_with_id():
    repo = FakeDeckRepository()
    deck = await CreateDeck(repo, FixedClock()).execute(" Travel ")
    assert deck.id == 1
    assert deck.name == "Travel"
    assert await ListDecks(repo).execute() == [deck]


async def test_create_deck_rejects_blank():
    with pytest.raises(EmptyDeckName):
        await CreateDeck(FakeDeckRepository(), FixedClock()).execute("  ")
```

`tests/application/test_import_use_case.py`:
```python
import pytest

from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.domain.shared.errors import DeckNotFound
from tests.conftest import FakeCardRepository, FakeDeckRepository, FixedClock


async def _deck(repo: FakeDeckRepository) -> int:
    from vocab_api.domain.deck.deck import Deck
    saved = await repo.add(Deck.create("Travel", FixedClock().now()))
    assert saved.id is not None
    return saved.id


async def test_dry_run_parses_without_persisting():
    decks, cards = FakeDeckRepository(), FakeCardRepository()
    deck_id = await _deck(decks)
    result = await ImportWords(decks, cards, FixedClock()).execute(
        deck_id, "run,rʌn,бежать", "csv", dry_run=True
    )
    assert result.committed is False
    assert [c.word for c in result.imported] == ["run"]
    assert await cards.count_due(deck_id, FixedClock().now()) == 0


async def test_commit_persists_valid_rows_and_returns_errors():
    decks, cards = FakeDeckRepository(), FakeCardRepository()
    deck_id = await _deck(decks)
    result = await ImportWords(decks, cards, FixedClock()).execute(
        deck_id, ",ipa,бежать\njump,dʒʌmp,прыгать", "csv", dry_run=False
    )
    assert result.committed is True
    assert [c.word for c in result.imported] == ["jump"]
    assert result.imported[0].id is not None
    assert [e.reason for e in result.errors] == ["empty word"]


async def test_missing_deck_raises():
    with pytest.raises(DeckNotFound):
        await ImportWords(FakeDeckRepository(), FakeCardRepository(), FixedClock()).execute(
            999, "run,бежать", "csv", dry_run=True
        )
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/application -v`
Expected: FAIL — use-case modules not found.

- [ ] **Step 4: Implement the use cases**

`src/vocab_api/application/use_cases/decks.py`:
```python
from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import DeckRepository
from vocab_api.domain.deck.deck import Deck


class CreateDeck:
    def __init__(self, decks: DeckRepository, clock: Clock) -> None:
        self._decks = decks
        self._clock = clock

    async def execute(self, name: str) -> Deck:
        return await self._decks.add(Deck.create(name, self._clock.now()))


class ListDecks:
    def __init__(self, decks: DeckRepository) -> None:
        self._decks = decks

    async def execute(self) -> list[Deck]:
        return await self._decks.list()
```

`src/vocab_api/application/use_cases/importing.py`:
```python
from dataclasses import dataclass

from vocab_api.application.importing.parser import Format, RowError, parse_words
from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, DeckRepository
from vocab_api.domain.card.card import Card


@dataclass(frozen=True, slots=True)
class ImportResult:
    imported: list[Card]
    errors: list[RowError]
    committed: bool


class ImportWords:
    def __init__(self, decks: DeckRepository, cards: CardRepository, clock: Clock) -> None:
        self._decks = decks
        self._cards = cards
        self._clock = clock

    async def execute(
        self, deck_id: int, raw: str, fmt: Format, dry_run: bool
    ) -> ImportResult:
        await self._decks.get(deck_id)  # raises DeckNotFound
        now = self._clock.now()
        parsed, errors = parse_words(raw, fmt)
        cards = [
            Card.create(deck_id, row.word, row.translation, now, row.transcription)
            for row in parsed
        ]
        if dry_run:
            return ImportResult(imported=cards, errors=errors, committed=False)
        saved = await self._cards.add_many(cards)
        return ImportResult(imported=saved, errors=errors, committed=True)
```

- [ ] **Step 5: Run the tests and mypy**

Run: `uv run pytest tests/application -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 6: Commit**

```bash
git add src/vocab_api/application/use_cases tests/conftest.py tests/application
git commit -m "feat(application): add deck and import use cases with fakes"
```

---

### Task 11: Use cases — `GetReviewQueue`, `RecordReview`, `GetStats`

**Files:**
- Create: `src/vocab_api/application/use_cases/review.py`, `src/vocab_api/application/use_cases/stats.py`, `tests/application/test_review_use_cases.py`, `tests/application/test_stats_use_case.py`

**Interfaces:**
- Consumes: `CardRepository`, `ReviewLogRepository`, `Scheduler`, `Clock`; `Card`, `Rating`, `ReviewLogEntry`, `CardNotFound`.
- Produces:
  - `GetReviewQueue(cards, clock)`: `async execute(deck_id: int, limit: int) -> list[Card]`.
  - `RecordReview(cards, logs, scheduler, clock)`: `async execute(card_id: int, rating: Rating) -> Card`. Loads the card (raises `CardNotFound`), computes new `FsrsState` via the scheduler, saves the updated card, appends a `ReviewLogEntry`, returns the updated card.
  - `Stats` frozen dataclass: `due_today: int`, `total_reviews: int`; `GetStats(cards, logs, clock)`: `async execute(deck_id: int) -> Stats`.

- [ ] **Step 1: Write the failing tests**

`tests/application/test_review_use_cases.py`:
```python
from datetime import timedelta

import pytest

from vocab_api.application.use_cases.review import GetReviewQueue, RecordReview
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.fsrs_state import FsrsState
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.shared.errors import CardNotFound
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeReviewLogRepository,
    FixedClock,
)


class StubScheduler:
    def review(self, state: FsrsState, rating: Rating, now):
        return FsrsState(due=now + timedelta(days=int(rating)), stability=1.0, last_review=now)


async def test_queue_returns_due_cards_only():
    cards = FakeCardRepository()
    await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    queue = await GetReviewQueue(cards, FixedClock()).execute(deck_id=1, limit=10)
    assert [c.word for c in queue] == ["run"]


async def test_record_review_updates_card_and_logs():
    cards, logs = FakeCardRepository(), FakeReviewLogRepository()
    (card,) = await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    assert card.id is not None
    updated = await RecordReview(cards, logs, StubScheduler(), FixedClock()).execute(
        card.id, Rating.GOOD
    )
    assert updated.fsrs.due == FIXED_NOW + timedelta(days=3)
    assert (await cards.get(card.id)).fsrs.stability == 1.0
    assert logs.entries[0].rating == Rating.GOOD


async def test_record_review_missing_card_raises():
    with pytest.raises(CardNotFound):
        await RecordReview(
            FakeCardRepository(), FakeReviewLogRepository(), StubScheduler(), FixedClock()
        ).execute(999, Rating.GOOD)
```

`tests/application/test_stats_use_case.py`:
```python
from vocab_api.application.use_cases.stats import GetStats
from vocab_api.domain.card.card import Card
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeReviewLogRepository,
    FixedClock,
)


async def test_stats_counts_due_and_reviews():
    cards, logs = FakeCardRepository(), FakeReviewLogRepository()
    await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    stats = await GetStats(cards, logs, FixedClock()).execute(deck_id=1)
    assert stats.due_today == 1
    assert stats.total_reviews == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/application/test_review_use_cases.py tests/application/test_stats_use_case.py -v`
Expected: FAIL — modules not found.

- [ ] **Step 3: Implement the use cases**

`src/vocab_api/application/use_cases/review.py`:
```python
from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, ReviewLogRepository
from vocab_api.application.ports.scheduler import Scheduler
from vocab_api.domain.card.card import Card
from vocab_api.domain.card.rating import Rating
from vocab_api.domain.review.review_log import ReviewLogEntry


class GetReviewQueue:
    def __init__(self, cards: CardRepository, clock: Clock) -> None:
        self._cards = cards
        self._clock = clock

    async def execute(self, deck_id: int, limit: int) -> list[Card]:
        return await self._cards.due(deck_id, self._clock.now(), limit)


class RecordReview:
    def __init__(
        self,
        cards: CardRepository,
        logs: ReviewLogRepository,
        scheduler: Scheduler,
        clock: Clock,
    ) -> None:
        self._cards = cards
        self._logs = logs
        self._scheduler = scheduler
        self._clock = clock

    async def execute(self, card_id: int, rating: Rating) -> Card:
        now = self._clock.now()
        card = await self._cards.get(card_id)  # raises CardNotFound
        updated = card.with_fsrs(self._scheduler.review(card.fsrs, rating, now))
        await self._cards.save(updated)
        await self._logs.add(ReviewLogEntry(card_id=card_id, rating=rating, reviewed_at=now))
        return updated
```

`src/vocab_api/application/use_cases/stats.py`:
```python
from dataclasses import dataclass

from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.repositories import CardRepository, ReviewLogRepository


@dataclass(frozen=True, slots=True)
class Stats:
    due_today: int
    total_reviews: int


class GetStats:
    def __init__(
        self, cards: CardRepository, logs: ReviewLogRepository, clock: Clock
    ) -> None:
        self._cards = cards
        self._logs = logs
        self._clock = clock

    async def execute(self, deck_id: int) -> Stats:
        due = await self._cards.count_due(deck_id, self._clock.now())
        reviews = await self._logs.count_reviews(deck_id)
        return Stats(due_today=due, total_reviews=reviews)
```

- [ ] **Step 4: Run the tests and mypy**

Run: `uv run pytest tests/application -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/application/use_cases tests/application
git commit -m "feat(application): add review and stats use cases"
```

---

### Task 12: HTTP layer + composition root

**Files:**
- Create: `src/vocab_api/config/__init__.py`, `src/vocab_api/config/settings.py`, `src/vocab_api/config/container.py`, `src/vocab_api/interfaces/__init__.py`, `src/vocab_api/interfaces/http/__init__.py`, `src/vocab_api/interfaces/http/errors.py`, `src/vocab_api/interfaces/http/dto.py`, `src/vocab_api/interfaces/http/deps.py`, `src/vocab_api/interfaces/http/decks_router.py`, `src/vocab_api/interfaces/http/review_router.py`, `src/vocab_api/interfaces/http/stats_router.py`, `apps/api/.env.example`, `tests/http/test_api_flow.py`
- Modify: `src/vocab_api/main.py`

**Interfaces:**
- Consumes: all use cases, `Database`, `SystemClock`, `PyFsrsScheduler`, all SQL repos, domain errors.
- Produces:
  - `Settings` (pydantic-settings): `database_url: str = "sqlite+aiosqlite:///./vocab.db"`.
  - `Container(settings)`: builds `Database`, `SystemClock`, `PyFsrsScheduler`, SQL repositories, and exposes ready use cases; `async init() -> None` calls `db.init()`.
  - Routes: `POST /decks`, `GET /decks`, `POST /decks/{deck_id}/import`, `GET /review/queue`, `POST /review`, `GET /stats`.

- [ ] **Step 1: Write the failing end-to-end test**

`tests/http/test_api_flow.py`:
```python
import httpx
import pytest

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.main import create_app


@pytest.fixture
async def client():
    container = Container(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    await container.init()
    app = create_app(container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_full_flow_create_import_review_stats(client: httpx.AsyncClient):
    deck = (await client.post("/decks", json={"name": "Travel"})).json()
    deck_id = deck["id"]

    preview = await client.post(
        f"/decks/{deck_id}/import",
        json={"raw": "run,rʌn,бежать", "format": "csv", "dry_run": True},
    )
    assert preview.json()["committed"] is False

    committed = await client.post(
        f"/decks/{deck_id}/import",
        json={"raw": "run,rʌn,бежать\njump,dʒʌmp,прыгать", "format": "csv", "dry_run": False},
    )
    assert committed.json()["committed"] is True
    assert len(committed.json()["imported"]) == 2

    queue = (await client.get("/review/queue", params={"deck_id": deck_id, "limit": 10})).json()
    assert len(queue) == 2
    first_id = queue[0]["id"]

    reviewed = await client.post("/review", json={"card_id": first_id, "rating": 3})
    assert reviewed.status_code == 200

    stats = (await client.get("/stats", params={"deck_id": deck_id})).json()
    assert stats["total_reviews"] == 1
    assert stats["due_today"] == 1  # one card reviewed and pushed out, one still due


async def test_import_into_missing_deck_returns_404(client: httpx.AsyncClient):
    resp = await client.post(
        "/decks/999/import", json={"raw": "run,бежать", "format": "csv", "dry_run": True}
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/http/test_api_flow.py -v`
Expected: FAIL — `Container`/`create_app(container)` not found.

- [ ] **Step 3: Implement settings, container, DTOs, error mapping, deps, routers, and app wiring**

`src/vocab_api/config/settings.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOCAB_", env_file=".env")
    database_url: str = "sqlite+aiosqlite:///./vocab.db"
```

`src/vocab_api/config/container.py`:
```python
from vocab_api.application.use_cases.decks import CreateDeck, ListDecks
from vocab_api.application.use_cases.importing import ImportWords
from vocab_api.application.use_cases.review import GetReviewQueue, RecordReview
from vocab_api.application.use_cases.stats import GetStats
from vocab_api.config.settings import Settings
from vocab_api.infrastructure.clock import SystemClock
from vocab_api.infrastructure.persistence.card_repo import SqlCardRepository
from vocab_api.infrastructure.persistence.deck_repo import SqlDeckRepository
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.review_log_repo import SqlReviewLogRepository
from vocab_api.infrastructure.scheduling.py_fsrs_scheduler import PyFsrsScheduler


class Container:
    def __init__(self, settings: Settings) -> None:
        self._db = Database(settings.database_url)
        clock = SystemClock()
        scheduler = PyFsrsScheduler()
        decks = SqlDeckRepository(self._db)
        cards = SqlCardRepository(self._db)
        logs = SqlReviewLogRepository(self._db)

        self.create_deck = CreateDeck(decks, clock)
        self.list_decks = ListDecks(decks)
        self.import_words = ImportWords(decks, cards, clock)
        self.get_review_queue = GetReviewQueue(cards, clock)
        self.record_review = RecordReview(cards, logs, scheduler, clock)
        self.get_stats = GetStats(cards, logs, clock)

    async def init(self) -> None:
        await self._db.init()
```

`src/vocab_api/interfaces/http/dto.py`:
```python
from typing import Literal

from pydantic import BaseModel


class CreateDeckIn(BaseModel):
    name: str


class DeckOut(BaseModel):
    id: int
    name: str


class ImportIn(BaseModel):
    raw: str
    format: Literal["csv", "markdown"]
    dry_run: bool = True


class CardOut(BaseModel):
    id: int | None
    word: str
    translation: str
    transcription: str | None


class RowErrorOut(BaseModel):
    line: int
    reason: str


class ImportOut(BaseModel):
    committed: bool
    imported: list[CardOut]
    errors: list[RowErrorOut]


class ReviewIn(BaseModel):
    card_id: int
    rating: Literal[1, 2, 3, 4]


class StatsOut(BaseModel):
    due_today: int
    total_reviews: int
```

`src/vocab_api/interfaces/http/errors.py`:
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from vocab_api.domain.shared.errors import (
    CardNotFound,
    DeckNotFound,
    DomainError,
)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DeckNotFound)
    async def _deck_not_found(_: Request, exc: DeckNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CardNotFound)
    async def _card_not_found(_: Request, exc: CardNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
```

`src/vocab_api/interfaces/http/deps.py`:
```python
from fastapi import Request

from vocab_api.config.container import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container
```

`src/vocab_api/interfaces/http/decks_router.py`:
```python
from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.card.card import Card
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import (
    CardOut,
    CreateDeckIn,
    DeckOut,
    ImportIn,
    ImportOut,
    RowErrorOut,
)

router = APIRouter(tags=["decks"])


def _card_out(card: Card) -> CardOut:
    return CardOut(
        id=card.id, word=card.word, translation=card.translation,
        transcription=card.transcription,
    )


@router.post("/decks", response_model=DeckOut)
async def create_deck(body: CreateDeckIn, c: Container = Depends(get_container)) -> DeckOut:
    deck = await c.create_deck.execute(body.name)
    assert deck.id is not None
    return DeckOut(id=deck.id, name=deck.name)


@router.get("/decks", response_model=list[DeckOut])
async def list_decks(c: Container = Depends(get_container)) -> list[DeckOut]:
    decks = await c.list_decks.execute()
    out: list[DeckOut] = []
    for d in decks:
        assert d.id is not None  # persisted decks always have an id
        out.append(DeckOut(id=d.id, name=d.name))
    return out


@router.post("/decks/{deck_id}/import", response_model=ImportOut)
async def import_words(
    deck_id: int, body: ImportIn, c: Container = Depends(get_container)
) -> ImportOut:
    result = await c.import_words.execute(deck_id, body.raw, body.format, body.dry_run)
    return ImportOut(
        committed=result.committed,
        imported=[_card_out(card) for card in result.imported],
        errors=[RowErrorOut(line=e.line, reason=e.reason) for e in result.errors],
    )
```

`src/vocab_api/interfaces/http/review_router.py`:
```python
from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.domain.card.rating import Rating
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import CardOut, ReviewIn

router = APIRouter(tags=["review"])


@router.get("/review/queue", response_model=list[CardOut])
async def review_queue(
    deck_id: int, limit: int = 20, c: Container = Depends(get_container)
) -> list[CardOut]:
    cards = await c.get_review_queue.execute(deck_id, limit)
    return [
        CardOut(id=card.id, word=card.word, translation=card.translation,
                transcription=card.transcription)
        for card in cards
    ]


@router.post("/review", response_model=CardOut)
async def record_review(body: ReviewIn, c: Container = Depends(get_container)) -> CardOut:
    card = await c.record_review.execute(body.card_id, Rating(body.rating))
    return CardOut(id=card.id, word=card.word, translation=card.translation,
                   transcription=card.transcription)
```

`src/vocab_api/interfaces/http/stats_router.py`:
```python
from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import StatsOut

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsOut)
async def stats(deck_id: int, c: Container = Depends(get_container)) -> StatsOut:
    result = await c.get_stats.execute(deck_id)
    return StatsOut(due_today=result.due_today, total_reviews=result.total_reviews)
```

Replace `src/vocab_api/main.py`:
```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.interfaces.http import decks_router, review_router, stats_router
from vocab_api.interfaces.http.errors import install_error_handlers


def create_app(container: Container | None = None) -> FastAPI:
    resolved = container or Container(Settings())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await resolved.init()
        yield

    app = FastAPI(title="Vocab Trainer API", lifespan=lifespan)
    app.state.container = resolved
    install_error_handlers(app)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(decks_router.router)
    app.include_router(review_router.router)
    app.include_router(stats_router.router)
    return app


app = create_app()
```

`apps/api/.env.example`:
```dotenv
VOCAB_DATABASE_URL=sqlite+aiosqlite:///./vocab.db
```

Note: the healthz test from Task 1 calls `create_app()` without a container; the default branch above keeps it working (lifespan only runs under a real server / `LifespanManager`, not the bare `ASGITransport` GET). Leave the Task 1 test unchanged.

- [ ] **Step 4: Run the whole suite, lint, and types**

Run:
```bash
uv run pytest -q
uv run ruff check .
uv run mypy
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/config src/vocab_api/interfaces src/vocab_api/main.py apps/api/.env.example tests/http/test_api_flow.py
git commit -m "feat(api): wire HTTP layer, composition root, and end-to-end flow"
```

---

### Task 13: Enforce architecture boundaries + finalize

**Files:**
- Create: `apps/api/.importlinter`, `apps/api/README.md`
- Verify: `.github/workflows/ci.yml` runs `lint-imports` (added in Task 1).

**Interfaces:**
- Produces: import-linter contracts that fail CI if the dependency rules are violated.

- [ ] **Step 1: Write the import-linter contracts**

`apps/api/.importlinter`:
```ini
[importlinter]
root_package = vocab_api

[importlinter:contract:layers]
name = Hexagonal layers
type = layers
layers =
    vocab_api.interfaces
    vocab_api.infrastructure
    vocab_api.application
    vocab_api.domain
containers =
    vocab_api

[importlinter:contract:domain-is-pure]
name = Domain imports no frameworks
type = forbidden
source_modules =
    vocab_api.domain
forbidden_modules =
    fastapi
    sqlmodel
    sqlalchemy
    fsrs
    httpx
    pydantic_settings

[importlinter:contract:application-uses-ports]
name = Application imports no adapters
type = forbidden
source_modules =
    vocab_api.application
forbidden_modules =
    vocab_api.infrastructure
    vocab_api.interfaces
    fastapi
    sqlmodel
    fsrs
```

- [ ] **Step 2: Run import-linter to verify it passes against the current code**

Run: `uv run lint-imports`
Expected: `Contracts: 3 kept, 0 broken.`

- [ ] **Step 3: Prove the contract bites (temporary negative check)**

Add `import sqlmodel` to the top of `src/vocab_api/domain/card/card.py`, then:

Run: `uv run lint-imports`
Expected: FAIL — the `domain-is-pure` contract is broken.
Then **revert** that line and re-run: `uv run lint-imports` → `3 kept, 0 broken`.

- [ ] **Step 4: Write a short README**

`apps/api/README.md`:
```markdown
# Vocab Trainer API

Hexagonal + DDD FastAPI backend for the Vocab Trainer.

## Run

```bash
cd apps/api
uv sync --dev
uv run uvicorn vocab_api.main:app --reload
```

## Checks

```bash
uv run ruff check .
uv run mypy
uv run lint-imports
uv run pytest -q
```

## Layout

- `domain/` — framework-free entities and value objects
- `application/` — use cases + ports
- `infrastructure/` — SQLModel, py-fsrs, clock adapters
- `interfaces/http/` — FastAPI routers
- `config/` — settings + composition root
```

- [ ] **Step 5: Full green run and commit**

Run:
```bash
uv run ruff check . && uv run mypy && uv run lint-imports && uv run pytest -q
```
Expected: all PASS.

```bash
git add apps/api/.importlinter apps/api/README.md
git commit -m "chore(api): enforce architecture boundaries and document setup"
```

---

## Definition of Done (Plan 1)

- `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`, `uv run lint-imports` all pass.
- `uv run uvicorn vocab_api.main:app` serves: create/list decks, import (dry-run + commit), review queue, record review, stats, healthz.
- Domain has zero framework imports (enforced). Every use case is unit-tested with fakes; the HTTP flow is covered end-to-end against in-memory SQLite.
- **Next:** Plan 2 (frontend, FSD) consumes this API; Plan 3 adds the LLM providers + sentence practice and pronunciation.
