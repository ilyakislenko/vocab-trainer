# Specs E & F — dark-mode contrast + i18n/number polish (implementation hand-off)

Self-contained spec for an implementing agent. The wider design is in
`2026-08-17-ux-overhaul-design.md`; **this doc is the executable version of its
E and F sections, updated to what is actually still open** (Spec A–D are done;
the hardcoded-English item of F was already resolved by Spec B).

**Rules (non-negotiable):** obey `CONTRIBUTING.md` — TypeScript `strict`, no
`any`, FSD boundaries, no dead code, match existing conventions. Every gate green
before "done": `pnpm lint` (Biome), `pnpm typecheck`, `pnpm fsd` (Steiger),
`pnpm test` (Vitest), `pnpm build`. Conventional Commits, personal identity only,
no tool/assistant attribution. Ship each spec as its own change set.

App context: a vocabulary spaced-repetition trainer (React 19 + TS, Feature-
Sliced Design) under `apps/web`. Theme tokens (light + dark, OKLCH) live in
`src/app/index.css`; the theme is toggled by a `dark` class on `<html>`.

---

## Spec E — dark-mode contrast

**Problem.** Components hardcode `bg-white`, which does **not** flip in dark mode.
Where the foreground is a theme token that goes light in dark mode
(`text-foreground`), you get white-on-white — invisible text. Nav/hover pairs
(`hover:bg-white hover:text-foreground`) go invisible on hover in dark mode.

**Exact sites** (verified 2026-08-17). Paths under `apps/web/src`.

Solid `bg-white` (fix all; ★ = confirmed invisible-text in dark):
- `entities/card/ui/CardFace.tsx:12` — chip, `text-primary`
- `widgets/skill-review-session/ui/SkillReviewSession.tsx:92` — `text-primary`
- ★ `widgets/skill-review-session/ui/SkillReviewSession.tsx:103` — **`text-foreground`**
- ★ `features/drill-word/ui/DrillChat.tsx:70` — **`bg-white text-foreground`** (chat bubble)
- `widgets/focus-list/ui/FocusList.tsx:23` — `text-destructive`
- `widgets/daily-plan/ui/DailyPlan.tsx:127` — `text-destructive`
- `widgets/placement-runner/ui/PlacementRunner.tsx:89` — `text-primary`
- `widgets/practice-session/ui/PracticeSession.tsx:160` — `text-primary`
- `widgets/onboarding/ui/Onboarding.tsx:24` — icon container (no text)

Hover pairs (invisible on hover in dark; fix all):
- `app/App.tsx:102`, `app/App.tsx:123`, `app/App.tsx:172` — `hover:bg-white hover:text-foreground`
- `widgets/practice-session/ui/PracticeSession.tsx:154` — `bg-white ... hover:bg-white/80`
- `widgets/practice-session/ui/PracticeSession.tsx:180` — `hover:bg-white hover:text-foreground`

Translucent (audit; lower risk, fix if it collides in dark):
- `features/check-sentence/ui/SentencePractice.tsx:93` — `bg-white/70`
- `features/interview/ui/InterviewChat.tsx:202` — `bg-white/90 text-black`
- `features/interview/ui/InterviewChat.tsx:240,247` — `bg-white/15`

**Fix.** Replace hardcoded white with theme-aware tokens so both themes stay
readable:
- Solid chip/pill `bg-white` → **`bg-background`** (white in light, near-black in
  dark; it sits on `bg-card`/`bg-tint-*` so it still stands out). Keep the colored
  `text-primary`/`text-destructive` (readable on both). For the two ★ sites the
  `text-foreground` is fine once the background is `bg-background` (that is the
  base fg/bg pair). The `DrillChat` bubble: use `bg-background text-foreground` (or
  `bg-muted`).
- `hover:bg-white` → **`hover:bg-muted`** (and drop the now-redundant
  `hover:text-foreground` or keep it — `text-foreground` on `bg-muted` is fine).
- Translucent overlays: if a dark-mode audit shows a collision, switch to a
  token-based translucency (e.g. `bg-foreground/10`); otherwise leave.

**Acceptance.**
1. Manually toggle dark mode and confirm every listed element has visible text.
2. Add a guard test (Vitest, or a simple repo check) asserting no component pairs
   a literal `bg-white` with `text-foreground`, and no `hover:bg-white` remains.
3. All gates green.

---

## Spec F — i18n consistency + number formatting

### F1. Fix the `practice.loading` namespace misuse
`practice.loading` is used as a generic loading string in unrelated widgets. It
renders the right text ("Loading…/Загрузка…"), so this is consistency, not a
visible bug — but it is wrong and fragile.

Add a shared key **`common.loading`** = `{ en: "Loading…", ru: "Загрузка…" }` in
`src/shared/lib/i18n.tsx`, and replace `t("practice.loading")` with
`t("common.loading")` at these **11 occurrences (8 files)**:
- `widgets/quiz-runner/ui/QuizRunner.tsx:20, 82`
- `widgets/review-session/ui/ReviewSession.tsx:54`
- `widgets/lesson-reader/ui/LessonReader.tsx:41, 122`
- `widgets/skill-review-session/ui/SkillReviewSession.tsx:31`
- `widgets/placement-runner/ui/PlacementRunner.tsx:22, 115`
- `widgets/curriculum-map/ui/CurriculumMap.tsx:129`
- `widgets/stats-panel/ui/StatsPanel.tsx:32`
- `widgets/practice-session/ui/PracticeSession.tsx:66`

Keep the existing `practice.loading` key (the Practice flow still legitimately
uses it) — do not delete it, just stop borrowing it elsewhere. (Lines 82/115/122
are "…isPending ? loading : submit" — same swap.)

### F2. Format large counts
There is no number formatting today (0 formatters). Counts can reach thousands
(due backlog, total reviews, per-level totals).

- Add `src/shared/lib/format.ts` exporting `formatCount(n: number, locale: "en" |
  "ru"): string` using `Intl.NumberFormat(locale)` (thousands separators). Unit-test it.
- Apply it to numeric displays in: `widgets/stats-panel` (due today, total
  reviews, by-state counts, activity), `widgets/daily-plan` (vocab_due/skill_due
  counts), `widgets/progress-dashboard` and `pages/profile` (totals, per-level
  completed/total). Pass the current `locale` from `useI18n()`.

### F3. Already done — do NOT redo
The previously-reported hardcoded English in `ImportPage`/`StatsPage`/`ImportPanel`
was resolved by the identity/onboarding change (now via the `no-deck` widget and
i18n). Verify it stays i18n'd; author nothing new there.

**Acceptance.** Loading strings resolve via `common.loading`; large counts render
with separators in both locales; a `formatCount` unit test; all gates green.

---

## Suggested order
E then F (independent; either can go first). Two small, reviewable commits — e.g.
`fix(ui): theme-aware surfaces for dark-mode contrast` and
`refactor(web): shared loading key + number formatting`.
