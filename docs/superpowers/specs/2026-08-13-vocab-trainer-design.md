# Vocab Trainer — Design Spec

**Date:** 2026-08-13
**Status:** Design approved; implementation plan pending

## 1. Purpose

A personal English-learning web app for a full-stack developer. It closes the full
loop for a self-curated vocabulary:

**import word lists → spaced-repetition review → construct sentences with LLM
feedback → practice pronunciation.**

Built to portfolio/showcase quality for a public GitHub repo.

## 2. Goals & Non-Goals

**Goals**
- Import own word lists (CSV, markdown table, or pasted text).
- Spaced repetition powered by FSRS.
- Sentence practice with LLM feedback: grammar, naturalness, corrected version, example.
- Pronunciation: hear a reference (TTS) and record self + speech-to-text comparison.
- Pluggable LLM provider switchable by config: Claude API / local model (Ollama) / none.
- Showcase quality: strict typing, tests, CI, clean docs.

**Non-goals (v1 — YAGNI)**
- Accounts / multi-user / auth.
- Cloud sync across devices.
- Native mobile apps.
- Phoneme-level pronunciation scoring (ELSA-style) — roadmap only.
- User-tunable FSRS parameters.

## 3. User & Primary Flow

Single user, self-hosted, desktop browser. Daily loop:
review due cards → for "mature but weak" cards, write a sentence and get feedback →
check pronunciation.

## 4. Architecture

Monorepo:

```
vocab-trainer/
  apps/api    FastAPI · Hexagonal (Ports & Adapters) + DDD · Python 3.12
  apps/web    Vite + React 19 · Feature-Sliced Design (FSD) · TypeScript
  packages/   generated TS client from the API's OpenAPI schema
```

- **Backend:** long-running Uvicorn server (self-hosted on the home server
  `192.168.1.100` via systemd/pm2). Not serverless.
- **Frontend:** static SPA build, served by nginx / any static host.
- **Cross-boundary type safety:** FastAPI emits an OpenAPI schema →
  codegen a typed TS client (`openapi-typescript` / orval). End-to-end typing without
  a shared runtime.

### 4.1 Backend — Hexagonal (Ports & Adapters) + DDD

Dependencies point inward. The **domain** layer has zero framework/IO imports
(no FastAPI, SQLModel, anthropic, or py-fsrs).

```
apps/api/src/
  domain/                pure business model — framework-free
    deck/                  Deck aggregate root
    card/                  Card aggregate root; FsrsState & Rating value objects
    practice/              SentenceAttempt entity; Feedback value object
    shared/                base types, domain errors
  application/           use cases + ports (interfaces)
    ports/                 DeckRepository, CardRepository, ReviewLogRepository,
                           SentenceAttemptRepository, LlmProvider, Scheduler, Clock
    use_cases/             import_words, get_review_queue, record_review,
                           check_sentence, suggest_example, get_stats
  infrastructure/        driven adapters (implement ports)
    persistence/           SQLModel tables + repositories + domain<->row mappers
    llm/                   Claude / Local / Null providers
    scheduling/            py-fsrs adapter behind the Scheduler port
  interfaces/            driving adapters
    http/                  FastAPI routers, request/response DTOs
  config/                settings + dependency wiring (composition root)
  main.py
```

- **Domain (DDD tactical):** `Card` is an aggregate root owning its FSRS state and
  review invariants; `Deck` is an aggregate root. Value objects: `Rating`
  (again/hard/good/easy), `FsrsState` (immutable), `Feedback`. Pure Python,
  unit-testable without IO.
- **Ports:** repository interfaces (one per aggregate) plus `LlmProvider`, `Scheduler`
  (FSRS), and `Clock`. Declared in `application/ports`; use cases depend only on these.
- **Adapters:** SQLModel repositories map aggregates to/from rows (the table shapes in
  §5 are the persistence adapter, kept separate from domain entities). LLM providers
  and the py-fsrs scheduler are driven adapters; FastAPI routers are driving adapters
  that invoke use cases.
- **Composition root:** `config` wires concrete adapters into use cases (via FastAPI
  `Depends` / a small container). Provider selection (§7) happens here.

### 4.2 Frontend — Feature-Sliced Design (FSD)

Layers import strictly downward (`app → pages → widgets → features → entities →
shared`). Each slice exposes a public API via `index.ts`; segments are
`ui / model / api / lib`.

```
apps/web/src/
  app/        providers (QueryClient, theme, router), global styles
  pages/      review, import, practice
  widgets/    ReviewSession, ImportPanel, PracticePanel, PronunciationBar
  features/   rate-card, import-words, check-sentence, play-tts, record-speech
  entities/   card, deck, sentence-attempt  (model + ui: CardFront / CardBack)
  shared/     ui (shadcn), api (generated client), lib, config
```

## 5. Data Model (SQLite via SQLModel)

These tables are the **persistence adapter** (infrastructure §4.1). Domain aggregates
are separate pure objects; repositories map between the two. Row shapes:

- `decks`: id, name, created_at.
- `cards`: id, deck_id (fk), word, transcription (nullable), translation, notes
  (nullable), section (nullable — source list tag, e.g. `main`/`international`/
  `elementary` from the Britlex seed), created_at, plus FSRS state (due, stability,
  difficulty, elapsed_days, scheduled_days, reps, lapses, state, last_review).
- `review_logs`: id, card_id (fk), rating (again/hard/good/easy), review_datetime,
  plus FSRS log fields (for stats and future optimization).
- `sentence_attempts`: id, card_id (fk), sentence, verdict (ok/needs_work), feedback,
  corrected (nullable), example (nullable), provider, created_at.

## 6. Backend API (FastAPI)

- `POST /decks`, `GET /decks`
- `POST /decks/{id}/import` — raw text + format hint + `dry_run` flag. With
  `dry_run=true` (default) it parses and returns a preview (rows + per-row errors)
  without writing; with `dry_run=false` it commits the parsed cards.
- `GET /review/queue?deck_id=&limit=` — due cards from py-fsrs.
- `GET /decks/{id}/cards?limit=&offset=&section=` — paginated listing of all cards in
  a deck, optionally filtered by section tag (practice mode "all words").
- `POST /review` — `{card_id, rating}` → updates FSRS state, writes a `review_log`.
- `POST /practice/check` — `{card_id, sentence}` → `LlmProvider.check_sentence` →
  `Feedback`; persists a `sentence_attempt`.
- `GET /practice/example?card_id=` — `LlmProvider.suggest_example`.
- `GET /practice/topic?deck_id=&topic=&limit=` — `LlmProvider.select_topic_words` →
  words matched against the deck via `CardRepository.by_words` (case-insensitive);
  practice mode "by topic".
- `GET /practice/hint?card_id=` — `LlmProvider.describe_word` → a learner-facing
  `WordHint` (meaning in Russian + an English example sentence); powers the word
  card in practice.
- `POST /practice/drill` — `{card_id, message}` → `LlmProvider.drill_word` →
  conversational response + follow-up question, keeping focus on the target word;
  enables "drill this word" mini-chat on the practice screen.
- `GET /stats` — basic counts (due today, reviewed, streak).
- `GET /healthz`.

All request/response bodies are Pydantic v2 models; validation happens at the boundary.

## 7. LLM Provider Abstraction

`LlmProvider` is an application **port** (§4.1); the three implementations are driven
**adapters**, chosen in the composition root via `LLM_PROVIDER`.

```python
class LlmProvider(Protocol):
    async def check_sentence(self, word: str, sentence: str) -> Feedback: ...
    async def suggest_example(self, word: str) -> str: ...
    async def select_topic_words(self, topic: str, limit: int) -> list[str]: ...
    async def describe_word(self, word: str) -> WordHint: ...
```

`select_topic_words` asks the model for single words related to a topic and
returns a JSON array (`OpenAiCompatibleProvider` parses tolerantly and clamps to
`limit`; `NullProvider` returns `[]` — topic practice is a no-op but never errors
offline). `describe_word` returns a `WordHint` (meaning in Russian + example
sentence); `NullProvider` returns a "disabled" hint and never errors.

Implementations (adapters):
- `ClaudeProvider` — `anthropic` SDK; API key from env, server-side only.
- `LocalProvider` — `httpx` to an OpenAI-compatible endpoint (Ollama on the RTX box
  `192.168.1.84`).
- `NullProvider` — offline: returns a deterministic "LLM disabled" result so the app
  stays usable for import / SRS / pronunciation.

Selected via `LLM_PROVIDER` env var (`claude` | `local` | `none`). Prompt lives in one
module. `Feedback` is a structured Pydantic model: `verdict`, `feedback`, `corrected`,
`example`.

## 8. Frontend (React 19)

Screens:
- **Import** — paste/upload → parse → preview table → confirm.
- **Review** — front (word) → reveal (transcription/translation) → 4 rating buttons;
  keyboard shortcuts (1–4, space); progress bar.
- **Practice** — three modes selected by tabs: **Due words** (the review queue,
  bounded by `limit`), **All words** (every card in the deck, with an optional
  **section filter** derived from the card tags), and **By topic** (a free-form
  prompt → LLM topic words intersected with the deck). Each mode feeds the same
  session: target word + hint, textarea, "Check" → feedback card (verdict,
  correction, example); optionally request an example first.
- **Pronunciation controls** on cards — 🔊 `speechSynthesis` (reference) and
  🎤 `SpeechRecognition` (record → compare transcript to target word → match/no-match).
- **Shell** — nav, dark/light theme (shadcn), deck selector.

Data fetching via TanStack Query against the generated typed client. Web Speech API is
feature-detected with a graceful fallback where unsupported.

## 9. Error Handling

- **API:** consistent error envelope; Pydantic validation → 422; provider errors → 502
  with a friendly message; `NullProvider` never errors.
- **Frontend:** TanStack Query loading/error states; toast on failure; Web Speech
  unsupported → disable control with a note.
- **Import:** per-row parse errors surfaced in the preview; never commit a partial set
  silently — preview then confirm.

## 10. Testing & Tooling

- **Backend:** pytest + httpx `AsyncClient`. The pure domain and use cases are unit-tested
  with in-memory fake adapters (no IO) — a direct payoff of the hexagonal boundaries;
  plus tests for the parser, the FSRS scheduler adapter, and each provider
  (`NullProvider` fully; Claude/Local via mocked transport).
- **Frontend:** Vitest + Testing Library (review flow, import preview) with a mocked client.
- **E2E:** Playwright — one happy path (import → review → practice with `NullProvider`).
- **Lint/format/types:** Ruff + mypy (strict) on Python; Biome + `tsc` on the web.
- **Architecture boundaries (enforced):** import-linter layer contracts (Python) and
  Steiger / FSD boundary lint (web) — see `CONTRIBUTING.md`.
- **CI:** GitHub Actions — lint, typecheck, test, build on push/PR.
- **Docs:** README (English) with setup, screenshots/GIF, `.env.example`, an architecture note.
- **Package managers:** uv (Python), pnpm (web).
- **Commits:** clean, no assistant/tool attribution.

## 11. Configuration

Server `.env`: `LLM_PROVIDER`, `ANTHROPIC_API_KEY`, `LOCAL_LLM_BASE_URL`,
`LOCAL_LLM_MODEL`, `DATABASE_URL`. A `.env.example` is committed.

## 12. Roadmap (post-v1)

- Phoneme-level pronunciation scoring (faster-whisper + wav2vec2 / forced alignment) —
  the reason the backend is Python.
- Local TTS models (higher quality than Web Speech).
- Multi-user + sync.
- FSRS parameter optimization from review history.
