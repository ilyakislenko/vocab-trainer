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
  apps/api    FastAPI (Python 3.12) · SQLModel + SQLite · py-fsrs · LlmProvider
  apps/web    Vite + React 19 (TS) · Tailwind + shadcn/ui · TanStack Query
  packages/   generated TS client from the API's OpenAPI schema
```

- **Backend:** long-running Uvicorn server (self-hosted on the home server
  `192.168.1.100` via systemd/pm2). Not serverless.
- **Frontend:** static SPA build, served by nginx / any static host.
- **Cross-boundary type safety:** FastAPI emits an OpenAPI schema →
  codegen a typed TS client (`openapi-typescript` / orval). End-to-end typing without
  a shared runtime.

## 5. Data Model (SQLite via SQLModel)

- `decks`: id, name, created_at.
- `cards`: id, deck_id (fk), word, transcription (nullable), translation, notes
  (nullable), created_at, plus FSRS state (due, stability, difficulty, elapsed_days,
  scheduled_days, reps, lapses, state, last_review).
- `review_logs`: id, card_id (fk), rating (again/hard/good/easy), review_datetime,
  plus FSRS log fields (for stats and future optimization).
- `sentence_attempts`: id, card_id (fk), sentence, verdict (ok/needs_work), feedback,
  corrected (nullable), example (nullable), provider, created_at.

## 6. Backend API (FastAPI)

- `POST /decks`, `GET /decks`
- `POST /decks/{id}/import` — raw text + format hint; parses CSV / markdown table;
  returns a preview, then commits on confirm.
- `GET /review/queue?deck_id=&limit=` — due cards from py-fsrs.
- `POST /review` — `{card_id, rating}` → updates FSRS state, writes a `review_log`.
- `POST /practice/check` — `{card_id, sentence}` → `LlmProvider.check_sentence` →
  `Feedback`; persists a `sentence_attempt`.
- `GET /practice/example?card_id=` — `LlmProvider.suggest_example`.
- `GET /stats` — basic counts (due today, reviewed, streak).
- `GET /healthz`.

All request/response bodies are Pydantic v2 models; validation happens at the boundary.

## 7. LLM Provider Abstraction

```python
class LlmProvider(Protocol):
    async def check_sentence(self, word: str, sentence: str) -> Feedback: ...
    async def suggest_example(self, word: str) -> str: ...
```

Implementations:
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
- **Practice** — target word + hint, textarea, "Check" → feedback card (verdict,
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

- **Backend:** pytest + httpx `AsyncClient`; unit tests for the parser, the FSRS wrapper,
  and each provider (`NullProvider` fully; Claude/Local via mocked transport).
- **Frontend:** Vitest + Testing Library (review flow, import preview) with a mocked client.
- **E2E:** Playwright — one happy path (import → review → practice with `NullProvider`).
- **Lint/format/types:** Ruff + mypy (strict) on Python; Biome + `tsc` on the web.
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
