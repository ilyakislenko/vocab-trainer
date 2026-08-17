# Content depth — generation tooling + new exercise types — design & hand-off

Grow the curriculum from a thin slice (~259 quiz items, ~6.3/module, mostly
mcq/cloze) into a deep, varied reinforcement set, via (A) an LLM-assisted
**generation tool** with human review and (B) **new exercise types**. The engine
change is small; the payoff is volume and variety.

**Owner decision (2026-08-17):** tooling **and** new exercise types.

**Rules:** obey `CONTRIBUTING.md`. Content is data (files); progress is DB.
Lessons are original prose; quiz items are **re-worded, never copied** from the
source books; **no copyrighted PDFs shipped**. Every addition is guarded by the
content-bundle test (`tests/infrastructure/test_curriculum_content.py`). The
generation tool is an offline dev tool (`apps/api/tools/`), not shipped in the app.

---

## 0. Baseline (verified 2026-08-17)
- Types today (`domain/curriculum/quiz.py`): `mcq`, `cloze`, `transform`,
  `error_correction` (all four exist and grade). 259 items over 41 modules.
- Bundle test asserts per available module: `len(items) >= 6` and `>= 2` types.
- LLM provider exists (`OpenAiCompatibleProvider`, Groq/local, env-switchable) +
  `NullProvider`. Tooling precedent: `tools/build_interview_bank.py`,
  `tools/britlex_pdf_to_markdown.py`.

## Part A — LLM-assisted item generation (dev tool + human review)

**Goal:** draft many candidate items per module from a topic/exercise **skeleton**,
then a human keeps/edits, so authoring scales without copying the books.

- New tool `apps/api/tools/generate_quiz_items.py`:
  - **Input:** a module id + its declared `skills` (from the lesson frontmatter) +
    a short **skeleton note** the owner supplies per module (the grammar point and
    a few example *structures* to cover — derived from the books, in the owner's
    words, **not** pasted exercises). Never feed copyrighted text in; feed the topic
    outline.
  - **Process:** call the existing LLM provider to draft N items of requested types,
    each with `id, type, skill (from the module's declared set), prompt, options/
    answers, explanation`. Prompt the model to **re-word**, vary structures, and
    tag each item with the target skill.
  - **Output:** a `*.draft.json` next to the module's quiz (never overwrites the
    live quiz). The tool does **not** commit anything.
- **Human review gate:** the owner reviews the draft, edits/culls, and only then the
  reviewed items are merged into the module's `quizzes/<id>.json`. Add a short
  `tools/README` step describing the review loop.
- **Guards (extend the content-bundle test / loader):**
  - every item's `skill` is in the lesson's declared skills (already enforced);
  - **no prompt contains its own answer** (the leak check from the placement work —
    generalise it to all quiz files);
  - mcq `answer_index` valid; cloze/transform/error_correction non-empty `answers`;
  - a lightweight duplicate check (no two items with identical prompt in a module).
- **Non-negotiable:** the tool assists; it never auto-publishes. Generated items are
  data adds, reviewed by a human, re-worded, copyright-safe.

## Part B — New exercise types

Add two types (the four current ones stay). Each new type touches the same four
layers; keep the engine general.

### B1. `word_order` (arrange tokens into a correct sentence)
- Content shape: `{ type:"word_order", skill, prompt, tokens:[...], answers:["the one
  correct ordering as a string"], explanation }`. `given` = the learner's ordered
  string (space-joined), graded by the existing normalise-and-compare path
  (extend `grade()` with a `word_order` branch; deterministic, pure).
- Frontend: a drag/click-to-order UI in the quiz runner; emits the ordered string.
- Tests: domain grade cases (correct, wrong order, extra space); content validation
  (non-empty `tokens`, `answers`); a Vitest UI test.

### B2. `listening` (hear a prompt, type or choose)
- Content shape: `{ type:"listening", skill, prompt (the sentence to speak via TTS),
  answers OR options/answer_index, explanation }`. Audio is produced by **TTS**
  (existing browser `speak`, or the pronunciation service's TTS) — **no audio files
  shipped** (copyright + repo size).
- Two sub-modes: dictation (type what you hear → cloze-style grading) or mcq
  (choose what you heard). Reuse existing grading; the only new bit is "play the
  prompt as audio, hide the text until answered".
- Frontend: a "play" control; the prompt text is revealed with the explanation.
- Optional tie-in: when the pronunciation-GOP service exists, a listening item can
  become a *speaking* item (say it, get scored) — but that lives in the
  pronunciation spec, not here.
- Tests: domain grade (dictation + mcq), validation, Vitest UI (play + reveal).

Each new type: add to `QuizItemType`, the `grade()` branch, `content_loader`
validation, the `PlacementItem`/quiz DTOs as needed, the quiz-runner renderer, and
tests. mypy strict, no `any`.

## Part C — Raise the depth bar

- Once the tool and types exist, grow modules and **raise the content-bundle
  minimums** in step (do not raise before the content is there, or CI breaks):
  target **≥ 12 items/module across ≥ 3 types** (owner may set higher). Update the
  test's `>= 6`/`>= 2` thresholds as coverage lands, module by module.
- Treat as an ongoing workstream (like Phase 6): each batch is a small reviewable
  PR of pure data, guarded by the test. Prioritise the modules the learner hits
  first (A2–B2 grammar) and the owner's weak spots.

## Non-goals
- No auto-published LLM content — human review is mandatory (quality + copyright).
- No shipped audio/PDF assets. Listening audio is TTS at runtime.
- No engine redesign — new types slot into the existing general loader/grader.
- Speaking/pronunciation scoring is the separate pronunciation-GOP spec.

## Sequencing
1. Part B types (`word_order`, `listening`) — engine + UI + tests, with a few seed
   items. 2. Part A generation tool + review loop. 3. Part C — drive volume up and
   raise the bundle-test minimums as content lands. A and B are independent; do
   whichever unblocks the owner first.
