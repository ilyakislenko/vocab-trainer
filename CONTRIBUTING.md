# Contributing & Engineering Standards

This repository holds a **strict quality bar**. The rules below are non-negotiable and
apply to every change — human or AI-assisted. Most of them are enforced mechanically in
CI (see [§9](#9-enforcement)); a change that violates them does not merge.

The guiding principle: **respect the architecture, prove your work, add nothing the spec
did not ask for.** When in doubt, re-read the design spec in
`docs/superpowers/specs/` and follow it. Do not silently improvise architecture.

---

## 1. Architecture is law

The backend is **Hexagonal (Ports & Adapters) + DDD**; the frontend is
**Feature-Sliced Design (FSD)**. The dependency rules are not stylistic — they are
enforced.

**Backend**
- `domain/` imports **nothing** from `application/`, `infrastructure/`, or
  `interfaces/`, and no framework/IO libraries (no FastAPI, SQLModel, `anthropic`,
  `httpx`, `py-fsrs`). Pure Python only.
- `application/` (use cases) depends **only on ports** (interfaces), never on concrete
  adapters. No SQLModel/HTTP/LLM types leak in.
- Concrete adapters live in `infrastructure/` (driven) and `interfaces/` (driving).
- Wiring happens **only** in the composition root (`config/`). No adapter is
  instantiated inside a use case or the domain.
- Business logic lives in the **domain and use cases** — never in FastAPI routers or in
  React components.

**Frontend (FSD)**
- Imports flow **strictly downward**: `app → pages → widgets → features → entities →
  shared`. No upward or sideways (same-layer) imports.
- A slice is used only through its **public API** (`index.ts`). Never deep-import another
  slice's internals.
- No business logic in UI components; it belongs in `*/model` or `features`.

These boundaries are checked by **import-linter** (Python) and **Steiger /
eslint FSD boundaries** (web). Do not add `# noqa`/`eslint-disable` to silence them —
fix the design.

## 2. Type safety

- Python: **mypy `--strict`**. No bare `Any`. No `# type: ignore` without a
  one-line justification comment.
- TypeScript: **`strict: true`**. No `any`, no non-null `!` to dodge the checker, no
  `@ts-ignore` without justification.
- Validate at every boundary: **Pydantic v2** on the API, **Zod/OpenAPI-generated
  types** on the web. Never trust unvalidated external input.

## 3. Code quality — no cutting corners

- **No placeholders in committed code**: no `TODO`, `FIXME`, `pass`-stub,
  `NotImplementedError`, `throw new Error("not implemented")`, or fake return values.
  If it isn't implemented, it isn't done — do not claim otherwise.
- **No dead or commented-out code**, no unused exports, imports, or parameters.
- **YAGNI**: do not add abstractions, config flags, endpoints, or "future-proofing"
  the spec did not ask for. (Respecting the chosen architecture is *not* over-engineering
  — that is the spec.)
- **Single responsibility**: small, focused functions and files. If a file or function
  grows hard to hold in your head, split it.
- **Intention-revealing names**; match existing conventions in the file/module.
- **No magic values** — name constants. **Early returns** over deep nesting.
- Do not reformat or refactor unrelated code in a feature change.

## 4. Testing — evidence over assertion

- Every use case has **unit tests using in-memory fake adapters** (no IO, no network,
  no real LLM). This is the payoff of the hexagonal boundaries — use it.
- Every bug fix ships with a **regression test** that fails before the fix.
- **Never claim work is complete without running** typecheck, lint, and tests and
  seeing them pass. Paste/observe the actual result — no "should work".
- Unit tests must not hit the network or a real model. Use fakes; `NullProvider` for the
  e2e happy path.
- Test behavior and edge cases, not implementation details or coverage vanity.

## 5. Scalability & performance

- **No N+1 queries.** Repositories fetch what a use case needs in as few queries as
  sensible. Index columns used in filters/sorts (`cards.due`, `cards.deck_id`).
- **All IO is async** (DB, `httpx`) — never block the event loop.
- **Paginate** list endpoints; the review queue is always bounded by `limit`.
- The HTTP layer is **stateless**; all state lives in the database.
- Ports are designed so a new adapter (another LLM, Postgres instead of SQLite) drops in
  **without touching the domain or use cases**. Never leak ORM/session objects past a
  repository.

## 6. Security

- **Secrets only via env**, never committed. Only `.env.example` is tracked.
- The LLM API key is **server-side only** and must never reach the browser or logs.
- Parameterized queries only (the ORM handles this — never build SQL by string).
- Never log secrets, tokens, or full request bodies containing them.

## 7. Errors

- No swallowed exceptions. Handle explicitly or propagate a **typed domain error**;
  the HTTP layer maps domain errors to status codes.
- Validation failures → `422`; upstream/provider failures → `502` with a safe message.
- `NullProvider` must never raise — the app stays usable with the LLM disabled.

## 8. Git & workflow

- Small, focused commits. **Conventional Commits** messages
  (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- Commits and code carry **no tool/assistant attribution**.
- Do **not** disable a lint/type/architecture rule to make CI pass — fix the root cause.
- If a task requires deviating from the spec or an architecturally significant choice,
  **stop and flag it** rather than guessing.

## 9. Enforcement

CI (GitHub Actions) blocks merge unless all pass:

| Gate | Backend | Frontend |
|------|---------|----------|
| Format & lint | Ruff | Biome |
| Types | mypy `--strict` | `tsc --noEmit` |
| Architecture boundaries | import-linter (layer contracts) | Steiger / FSD boundary lint |
| Tests | pytest | Vitest |
| E2E | — | Playwright (happy path) |
| Build | — | `vite build` |

Run these locally before pushing; pre-commit / lint-staged run the fast gates on commit.
