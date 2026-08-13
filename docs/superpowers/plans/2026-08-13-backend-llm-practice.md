# Vocab Trainer — Plan 3: Backend LLM + Sentence Practice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing hexagonal backend with a pluggable, **vendor-neutral** LLM layer and sentence-practice endpoints: submit a sentence built with a card's word and get structured feedback; request an example sentence; persist attempts.

**Architecture:** Same Hexagonal + DDD backend (`apps/api`). New domain (`SentenceAttempt`, `Feedback`), an `LlmProvider` port with two adapters — a `NullProvider` (offline) and one **OpenAI-compatible** provider (httpx → `/chat/completions`, works for both a hosted OpenAI-compatible endpoint and a local Ollama), selected by env. New `SentenceAttempt` persistence, use cases, and HTTP routes. No vendor SDK, **no Anthropic/OpenAI-branded classes** — the provider is named for the protocol it speaks.

**Tech Stack:** existing (Python 3.12, uv, FastAPI, SQLModel/SQLite async, Pydantic v2, pytest) + **httpx** (already a dependency) for the LLM HTTP calls.

## Global Constraints

- Extends `apps/api/`; run commands from `apps/api/`. Python `>=3.12`, **uv**.
- **Architecture is law** (enforced by import-linter): new `domain/practice/*` imports no framework/IO; `application/ports/llm.py` imports only `domain` + stdlib `typing`; the OpenAI-compatible provider (httpx) lives in `infrastructure/llm/`; wiring only in `config/`. The existing 3 import-linter contracts must still pass unchanged.
- **Vendor-neutral naming:** no class/module/env named `claude`, `anthropic`, or `openai`-the-vendor. The HTTP adapter is `OpenAiCompatibleProvider` (named for the wire protocol, which is an open de-facto standard) in `infrastructure/llm/openai_compatible_provider.py`. Env selector values are `api` | `none`.
- Types: mypy `--strict` clean; every `# type: ignore` justified. Quality: no placeholders. YAGNI.
- All LLM calls are server-side; the API key comes from env and is never returned to a client.
- Tests never hit a real network/model: `NullProvider` is tested directly; the OpenAI-compatible provider is tested with an injected `httpx.MockTransport`.
- Datetimes tz-aware UTC. Commits: Conventional Commits; **no assistant/tool attribution**.

## File Structure (additions to the existing backend)

```
apps/api/src/vocab_api/
  domain/practice/__init__.py
  domain/practice/feedback.py             # Verdict, Feedback
  domain/practice/sentence_attempt.py     # SentenceAttempt aggregate
  domain/shared/errors.py                 # + EmptySentence (edit)
  application/ports/llm.py                # LlmProvider port
  application/ports/repositories.py       # + SentenceAttemptRepository (edit)
  application/use_cases/practice.py       # CheckSentence, SuggestExample
  infrastructure/llm/__init__.py
  infrastructure/llm/null_provider.py     # NullProvider
  infrastructure/llm/openai_compatible_provider.py
  infrastructure/persistence/tables.py    # + SentenceAttemptRow (edit)
  infrastructure/persistence/mappers.py   # + sentence_attempt mappers (edit)
  infrastructure/persistence/sentence_attempt_repo.py
  interfaces/http/dto.py                   # + practice DTOs (edit)
  interfaces/http/practice_router.py
  config/settings.py                       # + LLM settings (edit)
  config/container.py                      # + provider + practice use cases (edit)
  main.py                                   # + practice_router (edit)
tests/  (mirror)
```

---

### Task 1: Domain — `Feedback`, `Verdict`, `SentenceAttempt`, `EmptySentence`

**Files:**
- Create: `src/vocab_api/domain/practice/__init__.py`, `src/vocab_api/domain/practice/feedback.py`, `src/vocab_api/domain/practice/sentence_attempt.py`, `tests/domain/test_sentence_attempt.py`
- Modify: `src/vocab_api/domain/shared/errors.py` (add `EmptySentence`)

**Interfaces:**
- Produces:
  - `Verdict(StrEnum)`: `OK = "ok"`, `NEEDS_WORK = "needs_work"`.
  - `Feedback` frozen dataclass: `verdict: Verdict`, `feedback: str`, `corrected: str | None = None`, `example: str | None = None`.
  - `EmptySentence(DomainError)`.
  - `SentenceAttempt` frozen dataclass: `card_id: int`, `sentence: str`, `feedback: Feedback`, `id: int | None = None`, `created_at: datetime | None = None`; `SentenceAttempt.create(card_id, sentence, feedback, now) -> SentenceAttempt` (strips sentence, raises `EmptySentence` if blank).

- [ ] **Step 1: Write the failing test**

`tests/domain/test_sentence_attempt.py`:
```python
from datetime import datetime, timezone

import pytest

from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.domain.shared.errors import EmptySentence

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)
FB = Feedback(verdict=Verdict.OK, feedback="Great.")


def test_create_trims_and_sets_created_at():
    attempt = SentenceAttempt.create(1, "  I run daily.  ", FB, NOW)
    assert attempt.sentence == "I run daily."
    assert attempt.feedback is FB
    assert attempt.created_at == NOW
    assert attempt.id is None


def test_blank_sentence_rejected():
    with pytest.raises(EmptySentence):
        SentenceAttempt.create(1, "   ", FB, NOW)


def test_verdict_values():
    assert (Verdict.OK, Verdict.NEEDS_WORK) == ("ok", "needs_work")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/domain/test_sentence_attempt.py -v` → FAIL (module not found).

- [ ] **Step 3: Implement**

`src/vocab_api/domain/practice/feedback.py`:
```python
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
```

Add to `src/vocab_api/domain/shared/errors.py`:
```python
class EmptySentence(DomainError):
    pass
```

`src/vocab_api/domain/practice/sentence_attempt.py`:
```python
from dataclasses import dataclass
from datetime import datetime

from vocab_api.domain.practice.feedback import Feedback
from vocab_api.domain.shared.errors import EmptySentence


@dataclass(frozen=True, slots=True)
class SentenceAttempt:
    card_id: int
    sentence: str
    feedback: Feedback
    id: int | None = None
    created_at: datetime | None = None

    @staticmethod
    def create(
        card_id: int, sentence: str, feedback: Feedback, now: datetime
    ) -> "SentenceAttempt":
        cleaned = sentence.strip()
        if not cleaned:
            raise EmptySentence()
        return SentenceAttempt(
            card_id=card_id, sentence=cleaned, feedback=feedback, created_at=now
        )
```

- [ ] **Step 4: Run tests + mypy**

Run: `uv run pytest tests/domain/test_sentence_attempt.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/domain/practice src/vocab_api/domain/shared/errors.py tests/domain/test_sentence_attempt.py
git commit -m "feat(domain): add Feedback and SentenceAttempt for practice"
```

---

### Task 2: `LlmProvider` port + `SentenceAttemptRepository` port + `NullProvider`

**Files:**
- Create: `src/vocab_api/application/ports/llm.py`, `src/vocab_api/infrastructure/llm/__init__.py`, `src/vocab_api/infrastructure/llm/null_provider.py`, `tests/infrastructure/test_null_provider.py`
- Modify: `src/vocab_api/application/ports/repositories.py` (add `SentenceAttemptRepository`)

**Interfaces:**
- Produces:
  - `LlmProvider(Protocol)`: `async def check_sentence(self, word: str, sentence: str) -> Feedback`; `async def suggest_example(self, word: str) -> str`.
  - `SentenceAttemptRepository(Protocol)`: `async def add(self, attempt: SentenceAttempt) -> SentenceAttempt`; `async def list_for_card(self, card_id: int) -> list[SentenceAttempt]`.
  - `NullProvider` implementing `LlmProvider` — deterministic, never raises, signals the LLM is disabled.

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_null_provider.py`:
```python
from vocab_api.domain.practice.feedback import Verdict
from vocab_api.infrastructure.llm.null_provider import NullProvider


async def test_null_provider_returns_disabled_feedback():
    provider = NullProvider()
    fb = await provider.check_sentence("run", "I run daily.")
    assert fb.verdict == Verdict.OK
    assert "disabled" in fb.feedback.lower()
    assert fb.corrected is None
    example = await provider.suggest_example("run")
    assert "run" in example
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/infrastructure/test_null_provider.py -v` → FAIL (module not found).

- [ ] **Step 3: Implement**

`src/vocab_api/application/ports/llm.py`:
```python
from typing import Protocol

from vocab_api.domain.practice.feedback import Feedback


class LlmProvider(Protocol):
    async def check_sentence(self, word: str, sentence: str) -> Feedback: ...
    async def suggest_example(self, word: str) -> str: ...
```

Add to `src/vocab_api/application/ports/repositories.py` (new class; keep existing imports, add `SentenceAttempt`):
```python
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt


class SentenceAttemptRepository(Protocol):
    async def add(self, attempt: SentenceAttempt) -> SentenceAttempt: ...
    async def list_for_card(self, card_id: int) -> list[SentenceAttempt]: ...
```

`src/vocab_api/infrastructure/llm/null_provider.py`:
```python
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.domain.practice.feedback import Feedback, Verdict


class NullProvider(LlmProvider):
    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        return Feedback(
            verdict=Verdict.OK,
            feedback="LLM feedback is disabled. Set LLM_PROVIDER=api to enable it.",
        )

    async def suggest_example(self, word: str) -> str:
        return f"(LLM disabled) Try writing a sentence with '{word}'."
```

- [ ] **Step 4: Run test + mypy**

Run: `uv run pytest tests/infrastructure/test_null_provider.py -v` → PASS; `uv run mypy` → Success (confirms `NullProvider` satisfies `LlmProvider`).

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/application/ports/llm.py src/vocab_api/application/ports/repositories.py src/vocab_api/infrastructure/llm tests/infrastructure/test_null_provider.py
git commit -m "feat(application): add LlmProvider port and NullProvider"
```

---

### Task 3: OpenAI-compatible provider (httpx)

**Files:**
- Create: `src/vocab_api/infrastructure/llm/openai_compatible_provider.py`, `tests/infrastructure/test_openai_compatible_provider.py`

**Interfaces:**
- Produces: `OpenAiCompatibleProvider(base_url: str, model: str, api_key: str | None = None, client: httpx.AsyncClient | None = None)` implementing `LlmProvider`. Calls `POST {base_url}/chat/completions` with the standard chat schema; `check_sentence` prompts for a JSON object and parses it leniently into `Feedback` (tolerates ```json fences; unknown/missing verdict → `NEEDS_WORK`; unparseable → a `NEEDS_WORK` Feedback whose `feedback` is the raw text). `suggest_example` returns the stripped completion text. If `client` is provided it is reused (and not closed); otherwise one is created per call and closed.

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_openai_compatible_provider.py`:
```python
import httpx

from vocab_api.domain.practice.feedback import Verdict
from vocab_api.infrastructure.llm.openai_compatible_provider import OpenAiCompatibleProvider


def _client(content: str) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_check_sentence_parses_json_feedback():
    content = '{"verdict":"needs_work","feedback":"Wrong tense.","corrected":"I ran.","example":"I run daily."}'
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    fb = await provider.check_sentence("run", "I runned.")
    assert fb.verdict == Verdict.NEEDS_WORK
    assert fb.corrected == "I ran."
    assert fb.example == "I run daily."


async def test_check_sentence_tolerates_code_fences():
    content = '```json\n{"verdict":"ok","feedback":"Good."}\n```'
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client(content))
    fb = await provider.check_sentence("run", "I run daily.")
    assert fb.verdict == Verdict.OK
    assert fb.corrected is None


async def test_check_sentence_falls_back_on_garbage():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("not json at all"))
    fb = await provider.check_sentence("run", "x")
    assert fb.verdict == Verdict.NEEDS_WORK
    assert "not json at all" in fb.feedback


async def test_suggest_example_returns_text():
    provider = OpenAiCompatibleProvider("http://x/v1", "m", client=_client("  She runs fast.  "))
    assert await provider.suggest_example("run") == "She runs fast."
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/infrastructure/test_openai_compatible_provider.py -v` → FAIL (module not found).

- [ ] **Step 3: Implement**

`src/vocab_api/infrastructure/llm/openai_compatible_provider.py`:
```python
import json
import re

import httpx

from vocab_api.application.ports.llm import LlmProvider
from vocab_api.domain.practice.feedback import Feedback, Verdict

_CHECK_SYSTEM = (
    "You are an English tutor. The learner is practising a target word. "
    "Judge whether their sentence uses the word correctly and naturally. "
    "Reply with ONLY a JSON object with keys: "
    '"verdict" ("ok" or "needs_work"), "feedback" (one short sentence), '
    '"corrected" (a corrected sentence, or null if none needed), '
    '"example" (a natural example sentence using the word).'
)
_EXAMPLE_SYSTEM = (
    "You are an English tutor. Reply with ONLY one short, natural example "
    "sentence that uses the given word. No preamble, no quotes."
)


class OpenAiCompatibleProvider(LlmProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._client = client

    async def _chat(self, system: str, user: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
        client = self._client or httpx.AsyncClient(timeout=30.0)
        try:
            response = await client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"])
        finally:
            if self._client is None:
                await client.aclose()

    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        raw = await self._chat(_CHECK_SYSTEM, f"Word: {word}\nSentence: {sentence}")
        return _parse_feedback(raw)

    async def suggest_example(self, word: str) -> str:
        return (await self._chat(_EXAMPLE_SYSTEM, f"Word: {word}")).strip()


def _parse_feedback(raw: str) -> Feedback:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            verdict = Verdict.OK if str(data.get("verdict")) == "ok" else Verdict.NEEDS_WORK
            return Feedback(
                verdict=verdict,
                feedback=str(data.get("feedback", "")).strip() or "No feedback.",
                corrected=_opt(data.get("corrected")),
                example=_opt(data.get("example")),
            )
        except (ValueError, TypeError):
            pass
    return Feedback(verdict=Verdict.NEEDS_WORK, feedback=raw.strip() or "No feedback.")


def _opt(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
```

- [ ] **Step 4: Run tests + mypy + ruff**

Run: `uv run pytest tests/infrastructure/test_openai_compatible_provider.py -v` → PASS (4 tests); `uv run mypy` → Success; `uv run ruff check .` → clean.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/infrastructure/llm/openai_compatible_provider.py tests/infrastructure/test_openai_compatible_provider.py
git commit -m "feat(infra): add OpenAI-compatible LLM provider adapter"
```

---

### Task 4: Persistence — `SentenceAttemptRow` + mapper + repository

**Files:**
- Create: `src/vocab_api/infrastructure/persistence/sentence_attempt_repo.py`, `tests/infrastructure/test_sentence_attempt_repo.py`
- Modify: `src/vocab_api/infrastructure/persistence/tables.py` (add `SentenceAttemptRow`), `src/vocab_api/infrastructure/persistence/mappers.py` (add `sentence_attempt_to_row` / `sentence_attempt_from_row`)

**Interfaces:**
- Produces:
  - `SentenceAttemptRow` (`table=True`, `__tablename__ = "sentence_attempts"`): `id`, `card_id` (index, fk `cards.id`), `sentence`, `verdict`, `feedback`, `corrected` (nullable), `example` (nullable), `created_at`.
  - `mappers.sentence_attempt_to_row` / `sentence_attempt_from_row` (verdict stored as its string value; rebuilt into `Feedback`).
  - `SqlSentenceAttemptRepository(db: Database)` implementing `SentenceAttemptRepository`: `add` (assigns id) and `list_for_card` (ordered by id).

- [ ] **Step 1: Write the failing test**

`tests/infrastructure/test_sentence_attempt_repo.py`:
```python
from datetime import datetime, timezone

from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.sentence_attempt_repo import (
    SqlSentenceAttemptRepository,
)

NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)


async def _repo() -> SqlSentenceAttemptRepository:
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init()
    return SqlSentenceAttemptRepository(db)


async def test_add_assigns_id_and_list_roundtrips_feedback():
    repo = await _repo()
    fb = Feedback(verdict=Verdict.NEEDS_WORK, feedback="Tense.", corrected="I ran.", example="I run.")
    saved = await repo.add(SentenceAttempt.create(1, "I runned.", fb, NOW))
    assert saved.id is not None
    listed = await repo.list_for_card(1)
    assert len(listed) == 1
    assert listed[0].sentence == "I runned."
    assert listed[0].feedback == fb
    assert await repo.list_for_card(999) == []
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/infrastructure/test_sentence_attempt_repo.py -v` → FAIL (module not found).

- [ ] **Step 3: Implement**

Add to `src/vocab_api/infrastructure/persistence/tables.py`:
```python
class SentenceAttemptRow(SQLModel, table=True):
    __tablename__ = "sentence_attempts"
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(index=True, foreign_key="cards.id")
    sentence: str
    verdict: str
    feedback: str
    corrected: str | None = None
    example: str | None = None
    created_at: datetime | None = None
```

Add to `src/vocab_api/infrastructure/persistence/mappers.py`:
```python
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.infrastructure.persistence.tables import SentenceAttemptRow


def sentence_attempt_to_row(attempt: SentenceAttempt) -> SentenceAttemptRow:
    return SentenceAttemptRow(
        id=attempt.id,
        card_id=attempt.card_id,
        sentence=attempt.sentence,
        verdict=attempt.feedback.verdict.value,
        feedback=attempt.feedback.feedback,
        corrected=attempt.feedback.corrected,
        example=attempt.feedback.example,
        created_at=attempt.created_at,
    )


def sentence_attempt_from_row(row: SentenceAttemptRow) -> SentenceAttempt:
    return SentenceAttempt(
        id=row.id,
        card_id=row.card_id,
        sentence=row.sentence,
        feedback=Feedback(
            verdict=Verdict(row.verdict),
            feedback=row.feedback,
            corrected=row.corrected,
            example=row.example,
        ),
        created_at=row.created_at,
    )
```

`src/vocab_api/infrastructure/persistence/sentence_attempt_repo.py`:
```python
from sqlmodel import select

from vocab_api.application.ports.repositories import SentenceAttemptRepository
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt
from vocab_api.infrastructure.persistence.engine import Database
from vocab_api.infrastructure.persistence.mappers import (
    sentence_attempt_from_row,
    sentence_attempt_to_row,
)
from vocab_api.infrastructure.persistence.tables import SentenceAttemptRow


class SqlSentenceAttemptRepository(SentenceAttemptRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, attempt: SentenceAttempt) -> SentenceAttempt:
        row = sentence_attempt_to_row(attempt)
        async with self._db.session() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return sentence_attempt_from_row(row)

    async def list_for_card(self, card_id: int) -> list[SentenceAttempt]:
        statement = (
            select(SentenceAttemptRow)
            .where(SentenceAttemptRow.card_id == card_id)
            .order_by(SentenceAttemptRow.id)  # type: ignore[arg-type]  # sqlmodel column, no mypy plugin
        )
        async with self._db.session() as session:
            result = await session.execute(statement)
            rows = result.scalars().all()
        return [sentence_attempt_from_row(row) for row in rows]
```

- [ ] **Step 4: Run tests + mypy**

Run: `uv run pytest tests/infrastructure/test_sentence_attempt_repo.py -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/infrastructure/persistence tests/infrastructure/test_sentence_attempt_repo.py
git commit -m "feat(infra): add sentence-attempt persistence"
```

---

### Task 5: Use cases — `CheckSentence`, `SuggestExample`

**Files:**
- Create: `src/vocab_api/application/use_cases/practice.py`, `tests/application/test_practice_use_cases.py`
- Modify: `tests/conftest.py` (add `FakeSentenceAttemptRepository` + a `StubLlmProvider`)

**Interfaces:**
- Consumes: `CardRepository`, `SentenceAttemptRepository`, `LlmProvider`, `Clock`; `Card`, `SentenceAttempt`, `Feedback`, `CardNotFound`.
- Produces:
  - `CheckSentence(cards, attempts, llm, clock)`: `async execute(card_id: int, sentence: str) -> SentenceAttempt` — loads the card (raises `CardNotFound`), calls `llm.check_sentence(card.word, sentence)`, builds+persists a `SentenceAttempt` (raises `EmptySentence` on blank), returns the saved attempt.
  - `SuggestExample(cards, llm)`: `async execute(card_id: int) -> str` — loads the card (raises `CardNotFound`), returns `llm.suggest_example(card.word)`.

- [ ] **Step 1: Add fakes to `tests/conftest.py`**

Append to `tests/conftest.py`:
```python
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt


class FakeSentenceAttemptRepository:
    def __init__(self) -> None:
        self._items: list[SentenceAttempt] = []

    async def add(self, attempt: SentenceAttempt) -> SentenceAttempt:
        stored = SentenceAttempt(
            id=len(self._items) + 1, card_id=attempt.card_id, sentence=attempt.sentence,
            feedback=attempt.feedback, created_at=attempt.created_at,
        )
        self._items.append(stored)
        return stored

    async def list_for_card(self, card_id: int) -> list[SentenceAttempt]:
        return [a for a in self._items if a.card_id == card_id]


class StubLlmProvider:
    def __init__(self, feedback: Feedback | None = None, example: str = "An example.") -> None:
        self._feedback = feedback or Feedback(verdict=Verdict.OK, feedback="Good.")
        self._example = example
        self.checked: list[tuple[str, str]] = []

    async def check_sentence(self, word: str, sentence: str) -> Feedback:
        self.checked.append((word, sentence))
        return self._feedback

    async def suggest_example(self, word: str) -> str:
        return self._example
```

- [ ] **Step 2: Write the failing tests**

`tests/application/test_practice_use_cases.py`:
```python
import pytest

from vocab_api.application.use_cases.practice import CheckSentence, SuggestExample
from vocab_api.domain.card.card import Card
from vocab_api.domain.practice.feedback import Feedback, Verdict
from vocab_api.domain.shared.errors import CardNotFound, EmptySentence
from tests.conftest import (
    FIXED_NOW,
    FakeCardRepository,
    FakeSentenceAttemptRepository,
    FixedClock,
    StubLlmProvider,
)


async def _card(cards: FakeCardRepository) -> int:
    (card,) = await cards.add_many([Card.create(1, "run", "бежать", FIXED_NOW)])
    assert card.id is not None
    return card.id


async def test_check_sentence_uses_card_word_and_persists():
    cards, attempts = FakeCardRepository(), FakeSentenceAttemptRepository()
    card_id = await _card(cards)
    llm = StubLlmProvider(Feedback(verdict=Verdict.NEEDS_WORK, feedback="Tense.", corrected="I ran."))
    saved = await CheckSentence(cards, attempts, llm, FixedClock()).execute(card_id, "I runned.")
    assert saved.id is not None
    assert saved.feedback.corrected == "I ran."
    assert llm.checked == [("run", "I runned.")]
    assert await attempts.list_for_card(card_id) == [saved]


async def test_check_sentence_blank_raises():
    cards, attempts = FakeCardRepository(), FakeSentenceAttemptRepository()
    card_id = await _card(cards)
    with pytest.raises(EmptySentence):
        await CheckSentence(cards, attempts, StubLlmProvider(), FixedClock()).execute(card_id, "  ")


async def test_check_sentence_missing_card_raises():
    with pytest.raises(CardNotFound):
        await CheckSentence(
            FakeCardRepository(), FakeSentenceAttemptRepository(), StubLlmProvider(), FixedClock()
        ).execute(999, "hi")


async def test_suggest_example_returns_llm_text():
    cards = FakeCardRepository()
    card_id = await _card(cards)
    example = await SuggestExample(cards, StubLlmProvider(example="She runs.")).execute(card_id)
    assert example == "She runs."
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/application/test_practice_use_cases.py -v` → FAIL (module not found).

- [ ] **Step 4: Implement**

`src/vocab_api/application/use_cases/practice.py`:
```python
from vocab_api.application.ports.clock import Clock
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.application.ports.repositories import (
    CardRepository,
    SentenceAttemptRepository,
)
from vocab_api.domain.practice.sentence_attempt import SentenceAttempt


class CheckSentence:
    def __init__(
        self,
        cards: CardRepository,
        attempts: SentenceAttemptRepository,
        llm: LlmProvider,
        clock: Clock,
    ) -> None:
        self._cards = cards
        self._attempts = attempts
        self._llm = llm
        self._clock = clock

    async def execute(self, card_id: int, sentence: str) -> SentenceAttempt:
        card = await self._cards.get(card_id)  # raises CardNotFound
        feedback = await self._llm.check_sentence(card.word, sentence)
        attempt = SentenceAttempt.create(card_id, sentence, feedback, self._clock.now())
        return await self._attempts.add(attempt)


class SuggestExample:
    def __init__(self, cards: CardRepository, llm: LlmProvider) -> None:
        self._cards = cards
        self._llm = llm

    async def execute(self, card_id: int) -> str:
        card = await self._cards.get(card_id)  # raises CardNotFound
        return await self._llm.suggest_example(card.word)
```

- [ ] **Step 5: Run tests + mypy**

Run: `uv run pytest tests/application -v` → PASS; `uv run mypy` → Success.

- [ ] **Step 6: Commit**

```bash
git add src/vocab_api/application/use_cases/practice.py tests/conftest.py tests/application/test_practice_use_cases.py
git commit -m "feat(application): add check-sentence and suggest-example use cases"
```

---

### Task 6: HTTP routes + settings + composition root

**Files:**
- Create: `src/vocab_api/interfaces/http/practice_router.py`, `tests/http/test_practice_flow.py`
- Modify: `src/vocab_api/interfaces/http/dto.py` (practice DTOs), `src/vocab_api/config/settings.py` (LLM settings), `src/vocab_api/config/container.py` (provider + practice use cases + attempt repo), `src/vocab_api/main.py` (include `practice_router`)

**Interfaces:**
- Consumes: `CheckSentence`, `SuggestExample`, `OpenAiCompatibleProvider`, `NullProvider`, `SqlSentenceAttemptRepository`.
- Produces:
  - `Settings` gains: `llm_provider: Literal["api", "none"] = "none"`, `llm_base_url: str = "http://localhost:11434/v1"`, `llm_model: str = "llama3.1"`, `llm_api_key: str | None = None` (env-prefixed `VOCAB_`).
  - `Container` gains `check_sentence` and `suggest_example` use cases, wired to `NullProvider` when `llm_provider == "none"` else `OpenAiCompatibleProvider(base_url, model, api_key)`.
  - Routes: `POST /practice/check` `{card_id, sentence}` → `FeedbackOut {verdict, feedback, corrected, example}`; `GET /practice/example?card_id=` → `ExampleOut {example}`.

- [ ] **Step 1: Write the failing end-to-end test**

`tests/http/test_practice_flow.py`:
```python
import httpx
import pytest

from vocab_api.config.container import Container
from vocab_api.config.settings import Settings
from vocab_api.main import create_app


@pytest.fixture
async def client():
    container = Container(Settings(database_url="sqlite+aiosqlite:///:memory:"))  # llm_provider defaults to "none"
    await container.init()
    transport = httpx.ASGITransport(app=create_app(container))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_check_and_example_with_null_provider(client: httpx.AsyncClient):
    deck = (await client.post("/decks", json={"name": "T"})).json()
    await client.post(
        f"/decks/{deck['id']}/import",
        json={"raw": "run,бежать", "format": "csv", "dry_run": False},
    )
    card = (await client.get("/review/queue", params={"deck_id": deck["id"], "limit": 5})).json()[0]

    checked = await client.post("/practice/check", json={"card_id": card["id"], "sentence": "I run."})
    assert checked.status_code == 200
    body = checked.json()
    assert body["verdict"] == "ok"
    assert "disabled" in body["feedback"].lower()

    example = await client.get("/practice/example", params={"card_id": card["id"]})
    assert example.status_code == 200
    assert "run" in example.json()["example"]


async def test_check_missing_card_404(client: httpx.AsyncClient):
    resp = await client.post("/practice/check", json={"card_id": 999, "sentence": "hi"})
    assert resp.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/http/test_practice_flow.py -v` → FAIL (`/practice/check` 404 / container has no `check_sentence`).

- [ ] **Step 3: Implement DTOs, settings, container, router, wiring**

Add to `src/vocab_api/interfaces/http/dto.py` (add `from vocab_api.domain.practice.feedback import Verdict` — interfaces→domain is a downward, import-linter-legal import, consistent with the routers already importing `Rating`/`Card`):
```python
class CheckSentenceIn(BaseModel):
    card_id: int
    sentence: str


class FeedbackOut(BaseModel):
    verdict: Verdict  # Pydantic serializes the StrEnum to "ok"/"needs_work"
    feedback: str
    corrected: str | None
    example: str | None


class ExampleOut(BaseModel):
    example: str
```

Add to `src/vocab_api/config/settings.py` `Settings`:
```python
    llm_provider: Literal["api", "none"] = "none"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.1"
    llm_api_key: str | None = None
```
(add `from typing import Literal` if missing.)

Add to `src/vocab_api/config/container.py` (`__init__`, after the existing wiring):
```python
from vocab_api.application.ports.llm import LlmProvider
from vocab_api.application.use_cases.practice import CheckSentence, SuggestExample
from vocab_api.infrastructure.llm.null_provider import NullProvider
from vocab_api.infrastructure.llm.openai_compatible_provider import OpenAiCompatibleProvider
from vocab_api.infrastructure.persistence.sentence_attempt_repo import SqlSentenceAttemptRepository
```
```python
        attempts = SqlSentenceAttemptRepository(self._db)
        provider: LlmProvider = (
            OpenAiCompatibleProvider(settings.llm_base_url, settings.llm_model, settings.llm_api_key)
            if settings.llm_provider == "api"
            else NullProvider()
        )
        self.check_sentence = CheckSentence(cards, attempts, provider, clock)
        self.suggest_example = SuggestExample(cards, provider)
```

`src/vocab_api/interfaces/http/practice_router.py`:
```python
from fastapi import APIRouter, Depends

from vocab_api.config.container import Container
from vocab_api.interfaces.http.deps import get_container
from vocab_api.interfaces.http.dto import CheckSentenceIn, ExampleOut, FeedbackOut

router = APIRouter(tags=["practice"])


@router.post("/practice/check", response_model=FeedbackOut)
async def check_sentence(body: CheckSentenceIn, c: Container = Depends(get_container)) -> FeedbackOut:
    attempt = await c.check_sentence.execute(body.card_id, body.sentence)
    fb = attempt.feedback
    return FeedbackOut(
        verdict=fb.verdict, feedback=fb.feedback, corrected=fb.corrected, example=fb.example
    )


@router.get("/practice/example", response_model=ExampleOut)
async def practice_example(card_id: int, c: Container = Depends(get_container)) -> ExampleOut:
    return ExampleOut(example=await c.suggest_example.execute(card_id))
```

In `src/vocab_api/main.py`, import and include the router alongside the others:
```python
from vocab_api.interfaces.http import decks_router, practice_router, review_router, stats_router
...
    app.include_router(practice_router.router)
```

- [ ] **Step 4: Run the whole gate**

Run:
```bash
uv run pytest -q
uv run ruff check .
uv run mypy
uv run lint-imports
```
Expected: all pass — including the new practice flow, and **import-linter still `3 kept, 0 broken`** (the new modules respect the layers: domain pure, application→ports only, httpx only in infrastructure).

- [ ] **Step 5: Commit**

```bash
git add src/vocab_api/interfaces/http src/vocab_api/config src/vocab_api/main.py tests/http/test_practice_flow.py
git commit -m "feat(api): wire practice routes and pluggable LLM provider"
```

- [ ] **Step 6: Update `.env.example`**

Append to `apps/api/.env.example`:
```dotenv
# LLM: "none" (offline NullProvider) or "api" (any OpenAI-compatible /chat/completions endpoint)
VOCAB_LLM_PROVIDER=none
VOCAB_LLM_BASE_URL=http://localhost:11434/v1
VOCAB_LLM_MODEL=llama3.1
# VOCAB_LLM_API_KEY=   # only needed for hosted endpoints
```
Commit:
```bash
git add apps/api/.env.example
git commit -m "docs: document LLM provider env settings"
```

---

## Definition of Done (Plan 3)

- `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`, `uv run lint-imports` all pass; import-linter still 3 kept / 0 broken.
- `POST /practice/check` and `GET /practice/example` work with `NullProvider` out of the box; setting `VOCAB_LLM_PROVIDER=api` + a base URL/model points at any OpenAI-compatible endpoint (Ollama on the RTX box, or a hosted gateway) with no code change.
- No vendor-branded (`claude`/`anthropic`/`openai`) class, module, or env name; the LLM key is server-side only.
- **Next:** Plan 4 (frontend) adds the practice UI (`features/check-sentence`) and pronunciation (`features/pronounce`, Web Speech) + a Practice page.
