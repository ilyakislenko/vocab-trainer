# UX/UI Overhaul — vocab-first review loop, onboarding, placement, polish

**Status:** design (approved to draft 2026-08-17). Supersedes two earlier
curriculum decisions on purpose (see Non-goals). Build to `CONTRIBUTING.md`;
this document only describes *what and why* — the architecture rules still win.

## 0. Context & the one decision that reframes everything

The app grew two half-connected worlds: a **vocabulary spaced-repetition
trainer** (decks → Review → Practice) and an **A1→C2 grammar curriculum**
(Learn → lessons/quizzes → Placement → Today). Most UX complaints are seams
between them.

**Owner decision (2026-08-17): the vocabulary SRS trainer is the product's
core.** Review + Practice are the daily loop and the landing. The curriculum
becomes a **secondary, optional** section ("Learn"), not the spine.

This **deliberately reverses**:
- §16 of `2026-08-16-english-curriculum-c2-design.md` ("onboarding routes a new
  learner through placement first") — placement becomes **opt-in**.
- §18 decision #3 ("Today is the post-onboarding landing") — **Review** is the
  landing; Today becomes an optional view inside Learn.

Do not "fix" these back — the demotion is intentional.

**Verified problems this spec addresses** (evidence gathered 2026-08-17):
- Imported cards are created due-now (`FsrsState.new` → `due = now`) and there is
  **no new-cards/day cap**, so seeded dictionaries surface ~9.7k cards as "due"
  (`Разминка 9858`, Stats `Новые 9758`). The number is meaningless and the queue
  is unusable.
- Review snapshots the queue once: **"Again" never re-shows in the session**, and
  on reload a 1–10-min card is not yet due → looks permanently gone. Good/Easy
  push cards days out and the empty queue reads as loss, not "scheduled".
- **No profile / identity surface** — the app never says who you are or your level.
- **Dark-mode contrast bug**: components hardcode `bg-white` (9 sites) that do not
  flip in dark theme → text/background collisions.
- **Placement** is a fixed 24-item deterministic set (memorizable), its cloze
  prompts **leak the answer** (`(fill in: was)`), there is **no per-question
  review** after the test, and the "highest level ≥70%" rule over-estimates.
- Polish: hardcoded English (`ImportPage`, `StatsPage`, `ImportPanel`), the wrong
  i18n key `practice.loading` reused in ~11 widgets, no Practice completion
  screen, no back-exit from Lesson/Review, unformatted large numbers.

## 1. Shape of the work

Six independently shippable specs, build in order **A → F**. Each: fully typed,
tested, boundary-clean, all gates green (Ruff, mypy strict, import-linter, Biome,
tsc, Steiger, Vitest, Playwright, vite build) before "done". No new placeholders,
no silenced lint/type/architecture rules. Bug fixes ship a regression test that
fails before the fix.

Constants are named (no magic numbers). New backend behaviour lives in the domain
/ use cases with unit tests over in-memory fakes; new frontend logic lives in
`*/model` or features, not components.

---

## Spec A — Review loop & new-card flow (fixes the reported bug)

**Outcome:** the daily review is a sane size, "Again" gives an immediate retry,
and an empty queue reads as "scheduled", never "lost".

### A1. New-cards-per-day cap
- Named constant `NEW_CARDS_PER_DAY` (default **20**), later surfaceable as a
  per-deck setting (not required now — YAGNI).
- The review queue is built as: **all genuinely-due cards** (state
  Learning/Review/Relearning with `due ≤ now`, uncapped) **plus at most
  `NEW_CARDS_PER_DAY − introduced_today`** brand-new (state New) cards, in a
  stable order (creation / id).
- `introduced_today` must be deterministic and testable. Recommended: add
  `Card.introduced_at: datetime | None`, set the first time a New card is
  reviewed (in `RecordReview`, when the prior state is New); count cards in the
  deck with `introduced_at` on/after local start-of-day. (An equivalent
  review-log–derived rule is acceptable if it is deterministic and unit-tested.)
- Counts shown to the user (Today warm-up, Stats "due today") reflect the
  **capped daily plan**, not the raw backlog. Optionally show "N new left in deck"
  as a separate, clearly-labelled number.
- **Tests:** domain/use-case — with 100 new + some due cards and cap 20, the queue
  yields the due cards + exactly 20 new; after introducing 20 today, a re-fetch
  yields 0 new; genuinely-due cards are never capped; day rollover resets the
  allowance.

### A2. In-session "Again" re-queue (frontend)
- `widgets/review-session` maintains a **working queue** instead of a fixed
  snapshot + index. On a rating: always persist via `RecordReview`; if the rating
  is **Again**, re-append the card to the end of the working queue so it reappears
  before the session ends. Good/Hard/Easy advance. Session ends when the working
  queue drains.
- A card may be re-queued repeatedly if answered Again again (Anki-like); that is
  acceptable and needs no cap.
- **Test:** Vitest — rating a card Again re-shows that same card later in the run;
  rating it Good removes it.

### A3. Honest per-rating feedback
- After a rating, show a brief inline interval hint: e.g. "Again — back in ~10 min",
  "Good — in 14 days", derived from the card's new FSRS due.
- **Backend touch:** `POST /review` currently returns only word fields; add the new
  `due` (ISO datetime) to its response DTO. Frontend converts to a coarse relative
  label ("~10 min", "3 days").
- **Tests:** pytest — the review response includes the updated `due`; Vitest — the
  hint renders for each rating.

### A4. "Готово" end/empty state
- When the working queue drains (or was empty): show **count reviewed**, **"next
  review in X"** (soonest upcoming `due` in the deck; `null` → "no upcoming
  reviews"), and a **"Practice more"** action → existing `/practice` (all-words).
  This replaces the bare "Nothing to practise 🎉".
- **Backend touch:** a soonest-due read — either `GET /review/summary?deck_id=`
  returning `{ next_due: datetime | null, reviewed_today: int }`, or fold
  `next_due` into the existing stats endpoint. Bounded, indexed on `cards.due`.
- **Tests:** pytest — soonest-due read returns the earliest future due (or null);
  Vitest — the end screen shows the count, next-due, and Practice-more link.

**Out of scope for A:** cross-deck interleaved review; changing FSRS parameters.

---

## Spec B — Identity & onboarding

**Outcome:** a new user is guided into the core loop, and the app can tell them
who they are and how they're doing.

### B1. Landing = Review; placement is opt-in
- `/` renders the Review flow (deck-scoped). Move Today to `/today` (optional,
  reachable from Learn). Remove the forced `→ /placement` redirect from
  `LearnPage`; placement is entered only from an explicit control (Learn / Profile).

### B2. Single, coherent first-run
- First-run trigger = **the user has no review history** (zero entries in
  `review_log` across all decks). This is a clean "brand-new user" signal that is
  robust to seeded dictionaries (which give decks but no reviews). Expose it as a
  small read (e.g. `has_reviewed: bool`, derivable from existing stats) rather than
  guessing from deck/card counts.
- One onboarding surface (reuse/extend `widgets/onboarding`): welcome → pick,
  create, or import a deck → land in Review. No competing second onboarding.

### B3. Profile page (`/profile`)
- A "who you are / how you're doing" surface:
  - estimated **level** (from `LearnerProfile.placement_level`; if unset →
    "not assessed" + a "Take the level test" CTA);
  - **streak**, **total reviews**, **cards by state** (reuse stats);
  - **curriculum progress** (reuse `/progress`: overall % + per-level bar);
  - an optional local display name (client-side only; no new PII server-side).
- Add a compact **level badge** in the header/sidebar so identity is always visible.
- Nav gains a **Profile** entry.

### B4. Consistent empty states
- `import`, `stats`, `practice`, `review` share one "no deck → guidance" pattern
  (same copy shape, all via i18n). No more mixed error-vs-onboarding-vs-redirect.

**Tests:** Vitest — landing is Review; Profile renders level/streak/progress with a
mocked client; "not assessed" path shows the CTA. Playwright happy path updated to
the new landing.

---

## Spec C — Navigation & the two-worlds seam

**Outcome:** one clear primary loop; Learn is a tidy optional section; no dead ends.

- **Simplify nav** to the core: Review · Practice · Learn · Profile (+ tools:
  Interview, Import, Stats). Today, skill-reviews, and the curriculum map live
  **under Learn**, not as competing top-level peers. Remove `/mascot` from any
  user-reachable surface (keep as dev-only or delete).
- **Skill reviews discoverable**: a clear entry inside Learn (and the Focus card),
  not only a corner button.
- **Back-exit** from Lesson and Review sessions (a visible "back to map" / "leave
  session" control), so neither is a one-way street.
- **Practice completion screen** for parity with Review/Quiz (end-of-run summary +
  what to do next).
- **Dedupe** the multiple "review" entry points into one obvious path.
- **One "what am I studying" model**: when a curriculum module links vocab
  (`/practice?section=`), make the target deck/section explicit in the UI so the
  learner isn't guessing which deck is active.

**Tests:** Vitest for the new completion screen and back-exit controls; Steiger
stays green (no boundary regressions).

---

## Spec D — Placement overhaul

**Outcome:** a test that stays challenging, explains itself, and estimates more
honestly.

### D1. Question pool + random sampling
- Expand `placement.json` into a **bank** of ≥ 12–15 items **per tested level**
  (A2–C1), same schema. `GetPlacement` **randomly samples** a fixed-size
  diagnostic (e.g. 6 per level) per attempt, so repeats are unique and not
  memorizable.
- Only the **selection** randomizes; **grading stays deterministic**. Inject the
  RNG (seedable) so tests are reproducible. The content-bundle validation extends
  to the larger bank (per-level minimum count, unique ids, valid enums).

### D2. Fix leaked answers
- Remove `(fill in: <answer>)` from every placement cloze prompt; replace with a
  neutral instruction (`(one word)` / `(two words)`). Apply the same scrub to any
  curriculum quiz cloze that embeds its answer. The correct answer stays only in
  the `answers` field. Add a validation/test that no prompt contains its own
  answer string.

### D3. Post-test review
- After grading, the response returns **per-item results**: the item, the learner's
  answer, the correct answer, correct/incorrect, and the explanation (for both
  right and wrong). The diagnostic `GET /placement` still ships **without**
  answers; only the **grade** response carries them (post-hoc reveal is fine).
- Frontend shows a scrollable review list after the level result, before "Start
  learning".

### D4. More honest level estimate
- Revisit the "highest level with ≥70%" rule (it labels B2 without requiring B1).
  Adopt a more conservative rule — recommended: **the highest level such that that
  level and every lower tested level each clear the threshold** (monotonic), with
  the threshold a named constant. Keep it deterministic and unit-tested. Document
  the chosen rule in the placement spec section.

**Tests:** domain — sampling picks the right shape and is seed-reproducible; the
monotonic estimate; no-leak assertion. HTTP — grade returns per-item review;
`GET /placement` still hides answers.

---

## Spec E — Theme / accessibility

**Outcome:** dark mode is readable everywhere.

- Replace hardcoded `bg-white` in components (≈ 9 sites: skill chips, option pills,
  etc.) with **theme-aware tokens** (`bg-card` / `bg-background` / a token that
  flips in dark mode). Audit text-on-tint pairs (`bg-tint-*` + `text-*`) for dark
  mode and fix any collision so foreground/background never match.
- Verify against the OKLCH tokens in `app/index.css`; the fix is in component
  usage, not just the tokens.
- **Tests:** a lightweight check (snapshot or explicit assertion) that the affected
  components use theme tokens, not literal white. Manual dark-mode pass noted in the
  PR.

---

## Spec F — i18n & polish (small)

**Outcome:** no stray English, consistent strings, humane numbers.

- Replace hardcoded English with i18n keys: `pages/import/ui/ImportPage.tsx:7`,
  `pages/stats/ui/StatsPage.tsx:5`, `widgets/import-panel/ui/ImportPanel.tsx:6`
  (add en/ru keys).
- Fix the `practice.loading` misuse in ~11 widgets: introduce a shared
  `common.loading` (or context-specific keys) and use it in review/quiz/placement/
  lesson/stats/skill-review/curriculum-map. (Currently renders correct text, so
  this is consistency, not a visible bug.)
- Format large counts (thousand separators or "999+") wherever counts can reach
  the thousands (stats, Today, progress).
- **Tests:** Vitest — no-deck states render translated copy in ru; a formatting
  helper unit test.

---

## Non-goals

- No FSRS algorithm/parameter changes (only *when* new cards enter).
- No cross-deck interleaved review (a bigger feature; out of scope).
- No server-side user accounts/PII (Profile display name is client-only).
- No new content authoring here — growing the item bank beyond the current 259
  quiz items is a separate content workstream (tracked, not part of A–F, except
  D1's placement bank which is required for the pool).

## Sequencing & handoff

Build **A → F**; A is the reported pain and unblocks a usable daily loop. Each spec
is a small, reviewable change set with its own tests and green gates, executable
independently by an implementing agent. Commit style: Conventional Commits, no
tool/assistant attribution, personal identity only.
