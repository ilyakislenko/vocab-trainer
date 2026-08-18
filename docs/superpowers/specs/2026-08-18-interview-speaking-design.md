# Interview speaking — pronounce interview phrases with per-phoneme feedback

Add a practice mode where the learner picks a curated **interview phrase**
(full-stack / frontend / AI), says the **whole sentence**, and gets the existing
per-word / per-phoneme pronunciation feedback. Hand-off spec for an implementing
agent.

**Why it's small:** the pronunciation pipeline is already live and already scores
sentences. Verified 2026-08-18: `POST /pronounce/score` with a multi-word target
("I built a React frontend") returns a per-word list, each word with its phonemes
and verdicts, and `PronounceAssessment` already renders that. So this feature is
**a phrase list + a screen that reuses the existing pronounce components** — no
new scoring code, no rtx/GOP changes.

**Rules:** obey `CONTRIBUTING.md` — FSD (imports flow down, slices used via their
public `index.ts`), TypeScript `strict`, no `any`, no business logic in
components, all gates green (Biome, tsc, Steiger, Vitest, build). No new
placeholders. Conventional Commits, personal identity only, no tool/assistant
attribution.

---

## 0. What already exists (reuse — do not rebuild)
- `features/pronounce`: `PronounceControls` (MediaRecorder → `useScorePronunciation`
  → `POST /api/pronounce/score`) and `PronounceAssessment` (overall % + per-word,
  per-phoneme scores/verdicts + weak-phoneme hint). `PronounceControls` takes a
  `target: string` — it already works for a full sentence.
- Backend `/pronounce/score` + the rtx GOP service score any target text
  (word or sentence). Live at `VOCAB_PRONUNCIATION_PROVIDER=rtx`.
- Interview *questions* exist (`seed/data/interview-questions.json`, the 2000-item
  bank) but they are Q&A for the mock-interview feature — **not** what this uses.

## Part A — Content: curated interview phrases

- New frontend data slice **`entities/interview-phrase`** (no backend, no DB — these
  are static reference strings the existing scorer consumes; progress isn't tracked).
  - `model/phrases.ts`: a typed list.
    ```ts
    export type PhraseCategory = "react" | "typescript" | "frontend" | "ai" | "backend" | "behavioral";
    export interface InterviewPhrase { id: string; category: PhraseCategory; text: string; }
    export const INTERVIEW_PHRASES: InterviewPhrase[] = [ /* … */ ];
    ```
  - Public API `index.ts` re-exports the type + list (+ a `phrasesByCategory` helper).
- **Author ~30–40 phrases**, original prose (natural things a candidate says in a
  full-stack/frontend/AI interview), spread across the categories, each one sentence,
  ~5–14 words (long enough to practice, short enough to say in one breath). Examples
  to set the tone (expand, don't just copy):
  - react: "I optimize re-renders with memoization and stable keys."
  - react: "I lift state up only when two components truly share it."
  - typescript: "I model the domain with discriminated unions and narrow at the boundaries."
  - frontend: "I care about accessibility, semantic HTML, and keyboard navigation."
  - frontend: "I measure performance with the browser profiler before optimizing."
  - ai: "I've integrated large language model APIs behind a provider interface."
  - ai: "I stream tokens to the client and handle provider failures gracefully."
  - backend: "I design REST endpoints to be stateless and paginated."
  - behavioral: "I'd start by clarifying the requirements and the success criteria."
  - behavioral: "When I disagree, I bring data and stay focused on the goal."
- **Guard test** (Vitest): every phrase has a unique id, a valid category, non-empty
  text of 3–20 words; every category has at least a few phrases.

## Part B — Screen: "Interview speaking"

- New page **`pages/interview-speaking`** at route `/speaking` (add the route in
  `app/App.tsx` and a nav entry, label via i18n `nav.speaking`).
- A widget **`widgets/phrase-practice`** (or keep it in the page if small):
  - a category filter (chips) + the phrase list for the selected category;
  - clicking a phrase selects it and shows it prominently;
  - renders `PronounceControls` with `target = selectedPhrase.text` → the learner
    records the whole sentence → `PronounceAssessment` shows the per-word /
    per-phoneme breakdown (highlighting weak phonemes exactly as today).
- Reuse `features/pronounce` through its public API; do not duplicate recording or
  scoring logic. No business logic in the components (selection state is UI state;
  the phrase data comes from the entity).
- i18n en/ru for all new copy (title, hint, category names, "pick a phrase", etc.).
- Keep it consistent with the app's visual style (cards, tints, rounded, dark-mode
  safe — use theme tokens, never literal `bg-white`).

## Testing
- Vitest: the phrase-data guard test (Part A); a screen test — renders phrases,
  selecting one shows the record control with that phrase as the target, and the
  assessment renders with a mocked `/pronounce/score` (MSW) returning a multi-word
  assessment. Steiger stays green (FSD boundaries).
- No backend tests (no backend change).

## Non-goals
- No progress tracking / scoring history for phrases (YAGNI — it's practice).
- No server-side phrase authoring or endpoint (frontend data is enough; revisit only
  if phrases need validation/linking like curriculum content).
- No changes to the GOP service, `/pronounce/score`, or the pronounce components'
  internals — only compose them.

## Sequencing
1. Part A (entity + phrases + guard test). 2. Part B (page + widget + nav + i18n +
   screen test). Small, reviewable; one or two commits.
