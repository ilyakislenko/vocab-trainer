# English Learning Path (Curriculum) — Design Spec

**Date:** 2026-08-16
**Status:** Design draft for hand-off to an implementing agent; awaiting owner review
**Builds on:** `docs/superpowers/specs/2026-08-13-vocab-trainer-design.md` (the existing
vocabulary/practice/interview app). This spec is **additive** — it introduces a new
Curriculum subsystem and wires it to the existing pillars (SRS review, sentence practice,
interview). It does not rewrite them.

> **Read first.** This spec is implemented under the repository's non-negotiable rules in
> `CONTRIBUTING.md` (architecture is law, mypy `--strict` / `tsc` strict, no placeholders,
> tests as evidence, YAGNI, FSD/Hexagonal boundaries enforced in CI). Where this spec and
> `CONTRIBUTING.md` disagree, **`CONTRIBUTING.md` wins** — stop and flag the conflict.

---

## 1. Purpose

Turn Elingo from a vocabulary+practice tool into a **complete, guided path from A1 to C2**
that a busy professional can walk a little each day and reach **active C1** (production, not
just recognition), with C2 reachable as the path's top.

The design goal stated by the owner: the app should be *"a benchmark of the ideal approach
to fast professional mastery of the language."* We interpret "ideal" not as "most features"
but as **the smallest system that applies the well-established mechanisms of language
learning**, each mapped to a concrete, testable feature (see §3). Everything else is YAGNI.

The subsystem is called the **Curriculum** (user-facing: **Learn**). It adds three things
the app lacks today:

1. **A readable knowledge layer** — authored lessons on grammar, prepositions, word order,
   phrasal verbs, collocations, etc. (Today there is nowhere to *read a rule*.)
2. **A guided route** — an ordered A1→C2 map that tells the learner exactly what to do next,
   so there is no "what should I study?" cognitive load.
3. **Retrieval + spaced repetition of rules** — every lesson is followed by quizzes; wrong
   answers become spaced-repetition items that resurface until mastered, and feed the
   existing practice/interview pillars.

---

## 2. Goals & Non-Goals

**Goals**
- An ordered curriculum **A1 → C2**, grouped by CEFR level, made of small **modules**.
- Each module = **readable lesson (markdown)** + **retrieval quiz** + links to source books
  and to the vocab/interview pillars.
- **Placement diagnostic** so a learner starts at the right level, not A1.
- **Retrieval practice** (testing effect): deterministic quiz grading in the domain.
- **Spaced repetition of skills**: failed quiz items become FSRS-scheduled *skill items*,
  reusing the existing `Scheduler` port and review mechanics.
- **A daily "Today" session** that interleaves due reviews + the next lesson/quiz + one
  production task (sentence or interview) + weak-spot focus — one screen, one clear
  "next action."
- **Free navigation, no gates**: open any authored module anytime; the route is a
  recommendation, not a lock; no score thresholds, no daily caps — gradual study is encouraged
  by presentation, not enforced.
- **Progress to C2** (always visible): per-module status and a level progress overview.
- **Content as versioned files** (markdown + JSON), loaded read-only at startup like the
  existing seed decks — so adding levels/modules is a *data* task, not a code change.
- Showcase quality: strict typing, hexagonal/FSD boundaries, tests, content-validation test.

**Non-Goals (v1 — YAGNI)**
- Accounts / multi-user / auth (single-user, consistent with the existing app).
- A prerequisite **skill-tree** graph — the path is **linear** (module order = the route).
  Skill-tree gating is explicitly deferred (roadmap).
- **LLM-generated learning paths** — the route and quizzes are authored and deterministic
  (Prove-it / testability). The LLM is used only for *optional* production feedback and
  optional open-answer grading, always with an offline fallback.
- Authentic **listening/audio** as an in-app pillar — the owner covers listening via a live
  online school + TTS conversation. A TTS "listen to the lesson example" nicety is allowed
  but not a graded pillar.
- Authoring **all** A1→C2 content in this project. The implementing agent builds the
  **engine** plus a **defined vertical slice of content** (§13). The rest is a data backlog
  that drops into the same schema.
- Phoneme-level pronunciation scoring (already roadmap in the base spec).

---

## 3. Pedagogical model → feature mapping

Each mechanism below is backed by a concrete, testable feature. This section is the "why";
later sections are the "how."

| Mechanism (learning science) | Feature in this spec |
|---|---|
| **Guided structure, low cognitive load** | Linear ordered modules; a single "next action" on the Today page (§10). |
| **Diagnostic placement** | Placement quiz sets starting level & current module (§9). |
| **Comprehensible input (i+1)** | Lessons are levelled; the route serves the next module at/just above current mastery. |
| **Retrieval practice / testing effect** | Every module ends in a quiz; recognition *and* production item types (§7). |
| **Spaced repetition** | Failed quiz items → FSRS **skill items**, reviewed by the existing scheduler (§8). |
| **Interleaving** | The Today session mixes reviews + new lesson + production across tracks (§10). |
| **Output + corrective feedback** | Module links a production task to the existing sentence-practice and interview pillars (§11). |
| **Adaptivity via weak-spot targeting** | "Leech" detection surfaces the most-failed skills in a Focus list (§8.4). Deterministic — not an LLM path. |
| **Motivation / habit** | Daily session, existing streaks, a visible A1→C2 progress bar (§12). |

---

## 4. Glossary (domain language — use these names)

- **Curriculum** — the whole ordered A1→C2 structure. Read-only, authored, versioned in git.
- **Level** — a CEFR band: `A1 A2 B1 B2 C1 C2`.
- **Track** — a strand a module belongs to: `grammar | vocabulary | phrasal_verbs |
  collocations | idioms | business`. (`functions`, for communicative can-do units, is a
  **reserved** enum value with no v1 content — do not build UI/logic specific to it until it
  has authored modules.)
- **Module** — the atomic step of the route: one topic at one level. Has one lesson and one
  quiz. Ordered within its level by `order`.
- **Lesson** — the readable markdown teaching document for a module.
- **QuizItem** — one retrieval question (typed: mcq / cloze / transform / error_correction).
- **SkillTag** — a stable id for the micro-skill an item drills (e.g. `prep.depend-on`,
  `wo.adverb-frequency`). Groups items and skill-items across modules; the unit of mastery.
- **SkillItem** — a spaced-repetition unit created when a learner fails a skill; FSRS-scheduled.
- **LearnerProfile** — the single learner's state: placement level + current module pointer.
- **ModuleProgress** — per-module status (not_started / in_progress / completed) + best score.
- **Session (Today)** — the assembled daily plan of concrete steps.
- **Placement** — the initial diagnostic that estimates the learner's level.

---

## 5. Architecture

Same shape as the base app: **Hexagonal + DDD** backend, **FSD** frontend. New code lives in
new slices; existing slices are extended only at their public edges.

### 5.1 Content lives in files, progress lives in the DB

This is the central architectural decision. The Curriculum **content** (levels, modules,
lessons, quiz items, placement) is **authored, read-only, versioned in git**, and loaded into
an **in-memory read-only repository** at startup — exactly like `JsonQuestionBank` loads
`interview-questions.json`. It is *not* stored in the database.

The **learner state** (profile, module progress, skill items, quiz attempts) **is** in the
database, because it is mutable per-use.

Rationale: content is not user data; putting it in files keeps it reviewable in PRs, diffable,
and free of migrations, and makes "add a level" a pure data change. It mirrors the existing
seed pattern and the `QuestionBank` precedent.

### 5.2 Backend layout (new files only shown)

```
apps/api/src/vocab_api/
  domain/
    curriculum/
      level.py            # Level value object / CEFR enum
      track.py            # Track enum
      module.py           # Module aggregate (id, level, track, order, title, refs, objectives)
      lesson.py           # Lesson value object (id, module_id, markdown, meta)
      quiz.py             # QuizItem + QuizItemType + a pure grade() function + GradeResult
      placement.py        # PlacementResult scoring (pure)
      skill_item.py       # SkillItem aggregate (reuses card.FsrsState + card.Rating)
      progress.py         # ModuleProgress, ModuleStatus, LearnerProfile
    # (existing: card/, deck/, practice/, review/, shared/)
  application/
    ports/
      curriculum_content.py   # CurriculumContent (read-only) Protocol
      curriculum_repos.py     # LearnerProfileRepository, ModuleProgressRepository,
                              # SkillItemRepository, QuizAttemptRepository (Protocols)
      # (reuse existing: scheduler.py, clock.py, llm.py)
    use_cases/
      curriculum.py       # GetCurriculumMap, GetModule, GetLesson, MarkLessonRead
      quiz.py             # GetModuleQuiz, GradeQuiz (schedules skill items on failure)
      placement.py        # GetPlacement, GradePlacement (sets profile level + current module)
      learning_session.py # BuildTodaySession
      skill_review.py     # GetSkillReviewQueue, RecordSkillReview (via Scheduler)
  infrastructure/
    curriculum/
      file_curriculum.py  # FileCurriculumRepository: loads seed/content/** into memory
      content_loader.py    # parse + validate the content bundle (frontmatter, JSON schema)
    persistence/
      curriculum_tables.py    # SQLModel rows: learner_profile, module_progress,
                              # skill_items, quiz_attempts
      learner_profile_repo.py
      module_progress_repo.py
      skill_item_repo.py
      quiz_attempt_repo.py
      curriculum_mappers.py
  interfaces/http/
    curriculum_router.py  # /curriculum/*, /placement/*
    quiz_router.py        # /curriculum/quiz/*
    session_router.py     # /session/today, /review/skills/*
    # (extend dto.py, deps.py, errors.py)
  config/
    curriculum_seed.py    # load_curriculum_content(); wired into Container
  seed/content/
    curriculum.json       # the manifest: levels → ordered module ids, metadata
    placement.json        # placement quiz items with level tags
    lessons/<module_id>.md # one markdown lesson per module (frontmatter + body)
    quizzes/<module_id>.json # quiz items per module
```

**Boundary rules (unchanged, CI-enforced):** `domain/curriculum/**` imports nothing from
`application/infrastructure/interfaces` and no IO/framework libs (pure Python). Use cases
depend only on the new ports (+ reused `Scheduler`, `Clock`, `LlmProvider`). The
`FileCurriculumRepository` and SQL repos are adapters, wired only in `config/container.py`.
Add the new packages to the **import-linter** contracts.

### 5.3 Frontend layout (FSD, new slices)

```
apps/web/src/
  pages/
    learn/        # curriculum map (levels → modules with status)
    lesson/       # a single lesson reader + "I've read this" + start quiz
    today/        # the daily session plan (the primary landing after onboarding)
    placement/    # the diagnostic flow
  widgets/
    curriculum-map/   # the A1→C2 board with progress
    lesson-reader/    # renders lesson markdown + references
    quiz-runner/      # runs a quiz, shows per-item feedback + explanation
    daily-plan/       # the Today steps list
  features/
    browse-curriculum/  # navigate the map (model: map query)
    read-lesson/        # mark-read mutation
    take-quiz/          # submit answers, grade, show results (model: grade mutation)
    placement-test/     # run + submit placement
    review-skills/      # the skill-item review analog of rate-card
  entities/
    curriculum/   # module/level/lesson view models + UI (ModuleCard, LevelSection)
    quiz/         # QuizItem view models + item renderers (mcq/cloze/…)
    skill-item/   # skill-item model + UI
    progress/     # progress model + ui (ProgressBar, StatusBadge)
  shared/
    ui/markdown/  # a sanitized markdown renderer (react-markdown + rehype-sanitize)
```

Imports flow downward only; every slice exposed via `index.ts`; data via TanStack Query over
the **regenerated** typed client (the OpenAPI client must be regenerated after the API changes).

### 5.4 Cross-cutting concerns (do not skip these)

- **DB schema creation — no migration framework.** The app has **no Alembic**; tables are
  created by `SQLModel.metadata.create_all` in `Database.init()`, and the table module is
  imported for its metadata side-effect (`engine.py` imports `persistence.tables` with
  `# noqa: F401`). The new `curriculum_tables.py` **must** likewise be imported so its tables
  are registered and auto-created. For adding a **column to an existing** table, follow the
  established in-place pattern (`Database._ensure_<x>_column` via `PRAGMA table_info` +
  `ALTER TABLE`). New tables need only registration; no ALTER.
- **Single-user identity.** There is no auth and no user concept (decks/reviews are not
  user-scoped today). `LearnerProfile` is a **singleton**: a get-or-create row (id = 1). **No
  `user_id` appears in any request/response.** All curriculum endpoints operate on that
  singleton implicitly, exactly as review/stats do today.
- **i18n (required).** The web app uses **i18next / `useTranslation`** (see `shared`, `app`).
  All new UI **chrome** (buttons, labels, statuses, page titles) must go through the existing
  i18n system with RU/EN keys — no hard-coded strings. **Lesson and quiz *content* is
  authored bilingually in the files themselves** (English target language + Russian
  explanations, as in the owner's cheat sheets) and is **not** routed through i18next.
- **Keyboard & a11y.** The review screen is keyboard-first (`1`–`4`, space). The `quiz-runner`
  must match: number keys select mcq options, Enter submits, and focus/ARIA are correct on
  every item type. Reuse existing `shared/ui` primitives.
- **Mascot (optional, on-brand — not required).** The app has an animated mascot with emotion
  states. The `quiz-runner`/Today flow **may** drive mascot emotions (correct → happy, streak
  → celebrate) by reusing the existing mascot entity's public API. This is a nicety, gated
  behind nothing; if skipped it changes no behaviour. Do **not** build new mascot machinery.
- **Answer payload DTO.** `POST /curriculum/quiz/grade` sends
  `answers: [{ item_id: str, value: str }]` — `value` is a plain string for every item type
  (for mcq it is the selected option index as a string). This matches the pure `grade(item,
  given: str)` signature and keeps the DTO mypy-strict clean (no unions).

---

## 6. Content model & file formats

The implementing agent must build loaders/validators to **exactly** these formats. Examples
are normative.

### 6.1 `seed/content/curriculum.json` — the manifest

```jsonc
{
  "version": 1,
  "levels": [
    {
      "level": "B2",
      "modules": [
        "b2.grammar.perfect-aspect",
        "b2.prep.dependent-prepositions",
        "b2.phrasal.work-business"
      ]
    },
    { "level": "C1", "modules": ["c1.grammar.inversion", "c1.collocations.academic"] }
  ]
}
```

- `levels` is ordered A1→C2; each level lists its module ids **in route order**.
- A module id is `"<level>.<track>.<slug>"`, globally unique, stable (used as a DB key).
- The manifest **always lists the complete A1→C2 module ladder** so the whole route is visible
  from day one. A module whose lesson/quiz files are **not yet authored** is listed as an
  object `{ "id": "a1.grammar.to-be", "status": "authoring" }` instead of a bare id; the map
  shows it as *"being added"* (visible in the ladder, not yet openable). This is a **temporary
  build-order state on the way to full coverage — not a permanent gap.** A bare string implies
  `status: "available"` and **must** have a lesson + quiz on disk (enforced by §6.5). As files
  land, the entry flips to `available` with no code change.

### 6.2 `seed/content/lessons/<module_id>.md` — a lesson

YAML frontmatter + markdown body. Body is authored teaching prose (original wording — never
copied from the source books; the books are a *topic skeleton* only).

```markdown
---
id: b2.prep.dependent-prepositions
title: Dependent prepositions (depend on, responsible for)
level: B2
track: grammar
estimated_minutes: 8
objectives:
  - "Use the correct preposition after common verbs/adjectives/nouns."
skills: [prep.depend-on, prep.responsible-for, prep.interested-in]
references:
  - { book: "English Grammar in Use (Murphy)", locator: "Units 133–136" }
  - { book: "Grammar Reference (Kuzmin)", locator: "Prepositions" }
---

Some words demand a fixed preposition you cannot derive from logic — you memorise the pair…

| Correct | Common mistake |
|---|---|
| depend **on** | ~~depend from~~ |
```

- `skills` lists the `SkillTag`s the lesson teaches; **every** quiz item's `skill` must be one
  of these (validated at load).
- `references.locator` is free text; it is a pointer for the learner, not a deep link.

### 6.3 `seed/content/quizzes/<module_id>.json` — retrieval items

```jsonc
{
  "module_id": "b2.prep.dependent-prepositions",
  "items": [
    {
      "id": "b2.prep.dependent-prepositions.q1",
      "type": "mcq",
      "skill": "prep.depend-on",
      "prompt": "The result ___ the configuration.",
      "options": ["depends on", "depends from", "depends of", "depends to"],
      "answer_index": 0,
      "explanation": "Fixed pair: depend **on**."
    },
    {
      "id": "b2.prep.dependent-prepositions.q2",
      "type": "cloze",
      "skill": "prep.responsible-for",
      "prompt": "Who is responsible ___ the deployment?",
      "answers": ["for"],
      "explanation": "responsible **for**."
    },
    {
      "id": "b2.prep.dependent-prepositions.q3",
      "type": "error_correction",
      "skill": "prep.interested-in",
      "prompt": "I'm interested about backend performance.",
      "answers": ["I'm interested in backend performance."],
      "llm_gradable": true,
      "explanation": "interested **in**."
    }
  ]
}
```

**Item types (v1):**
- `mcq` — one correct option (`answer_index`). Graded deterministically.
- `cloze` — free-text gap; graded case-insensitively, trimmed, against `answers[]`
  (accepted variants listed explicitly). Deterministic.
- `transform` — rewrite to an instruction; graded against normalised `answers[]`
  (lowercase, collapse whitespace, strip terminal punctuation). Deterministic.
- `error_correction` — fix the sentence; graded against normalised `answers[]` first
  (deterministic). If it misses **and** `llm_gradable: true` **and** the LLM is enabled, an
  optional LLM check may accept a semantically-correct variant. **Offline (`NullProvider`) it
  is graded by `answers[]` only and never errors** (§CONTRIBUTING §7).

Grading normalisation and the accepted-answer comparison are **pure domain functions**
(`domain/curriculum/quiz.py::grade`), unit-tested exhaustively. The LLM path is an optional
adapter call layered in the *use case*, never in the domain.

### 6.4 `seed/content/placement.json`

A fixed bank of level-tagged items (reusing the quiz item schema) used by the diagnostic:

```jsonc
{
  "items": [
    { "id": "pl.1", "level": "A2", "type": "mcq", "skill": "…", "prompt": "…",
      "options": ["…"], "answer_index": 1 }
  ]
}
```

### 6.5 Content validation (required test)

A test (`tests/infrastructure/test_content_bundle.py`) loads the whole bundle and asserts:
module ids unique and match `curriculum.json`; **every `available` module has exactly one
lesson and one quiz file (and `planned` stubs have neither)**; every quiz item's `skill` is
declared in its lesson's `skills`; mcq has a valid `answer_index`;
cloze/transform/error_correction have non-empty `answers`; `level`/`track` are valid enums;
all `module_id`s in quiz files resolve. This is both a correctness gate and a showcase piece
(content can't silently rot).

---

## 7. Domain model (pure)

Illustrative shapes (final signatures at the implementer's discretion, but names and purity
are fixed). Reuse existing value objects where noted.

```python
# domain/curriculum/level.py
class Level(str, Enum):
    A1="A1"; A2="A2"; B1="B1"; B2="B2"; C1="C1"; C2="C2"
    def order(self) -> int: ...   # A1<A2<…<C2, for comparisons

# domain/curriculum/module.py
@dataclass(frozen=True)
class Module:
    id: str; level: Level; track: Track; order: int
    title: str; objectives: tuple[str, ...]
    skills: tuple[str, ...]; references: tuple[Reference, ...]

# domain/curriculum/quiz.py
class QuizItemType(str, Enum): MCQ="mcq"; CLOZE="cloze"; TRANSFORM="transform"; ERROR_CORRECTION="error_correction"

@dataclass(frozen=True)
class QuizItem:
    id: str; module_id: str; type: QuizItemType; skill: str
    prompt: str; explanation: str
    options: tuple[str, ...] | None; answer_index: int | None
    answers: tuple[str, ...] | None; llm_gradable: bool

@dataclass(frozen=True)
class GradeResult:
    item_id: str; skill: str; correct: bool; needs_llm: bool  # true when deterministic miss & llm_gradable

def grade(item: QuizItem, given: str) -> GradeResult: ...
# pure; no LLM. `given` is always a string: for mcq it is the selected option index as a
# string ("0".."n-1"); for cloze/transform/error_correction it is the learner's text.
# Keeping one type avoids a str|int union (mypy-strict clean).

# domain/curriculum/skill_item.py
@dataclass
class SkillItem:                 # a spaced-repetition unit for a micro-skill
    id: int | None; skill: str; module_id: str; source_item_id: str
    fsrs: FsrsState              # REUSES domain/card/fsrs_state.py
    @staticmethod
    def create(skill: str, module_id: str, source_item_id: str, now: datetime) -> "SkillItem": ...
    def review(self, rating: Rating, scheduler_out: FsrsState) -> None: ...  # mirrors Card

# domain/curriculum/progress.py
class ModuleStatus(str, Enum): NOT_STARTED="not_started"; IN_PROGRESS="in_progress"; COMPLETED="completed"

@dataclass
class ModuleProgress:
    module_id: str; status: ModuleStatus
    lesson_read_at: datetime | None; quiz_best_score: float | None; completed_at: datetime | None

@dataclass
class LearnerProfile:
    placement_level: Level | None; current_module_id: str | None
```

**Navigation & completion rule (fixed):** navigation is **free** — any `available` module can be
opened at any time; the route order is a **recommendation, not a gate**. There is **no score
threshold and no daily cap** anywhere. A module is:
- `in_progress` once its lesson is read;
- `completed` once its lesson is read **and** its quiz has been attempted at least once (any
  score — the score is shown for information/adaptivity, never to block).

`LearnerProfile.current_module_id` is the **recommended next** module (the first
not-`completed` `available` module in `curriculum.json` order), surfaced as a suggestion on the
Today page. The learner may ignore it and open any module directly; opening a module never
requires finishing another. Gradual, in-order study is *encouraged by presentation*, not
enforced. All of this is computed by pure functions and use cases, not the UI.

---

## 8. Spaced repetition of skills (reusing FSRS)

### 8.1 Reuse, don't duplicate
The existing `Scheduler` port (py-fsrs adapter) and the `FsrsState`/`Rating` value objects are
reused verbatim. We introduce a **separate reviewable aggregate** `SkillItem` with its own
table and repository, rather than overloading the vocab `Card` aggregate (which is
word-shaped: word/translation/transcription). This keeps `Card` intact (DDD) while sharing the
scheduling machinery.

### 8.2 Creating skill items
`GradeQuiz` (§ use cases): for each item the learner got wrong, **upsert** a `SkillItem` for
that `skill` (one per skill, not per item) via `SkillItemRepository`, initialised due-now.
Correct answers on an existing skill item are optionally recorded as a `Good` review (so
mastery decays correctly). This is the bridge that makes reading→quiz→spaced-repetition close
the loop.

### 8.3 Reviewing skill items
`GetSkillReviewQueue` returns due skill items (bounded by `limit`, indexed on `fsrs_due`).
`RecordSkillReview({skill_item_id, rating})` runs the same `Scheduler.review(...)` path as
vocab review and persists new FSRS state. The front-end review flow (`review-skills` feature)
mirrors `rate-card`: it shows the skill's prompt/example, reveals the answer/explanation, then
`Again/Hard/Good/Easy`. The Today page can present vocab-card reviews and skill-item reviews in
one interleaved queue.

### 8.4 Weak-spot ("Focus") detection — deterministic adaptivity
A skill is a **leech** when its `SkillItem.fsrs.lapses ≥ 4` (a named constant, mirror FSRS
convention). `GetTodaySession` (and a small `/session/focus` read) surfaces the top-N leeches
so the learner can drill exactly what keeps failing. This is the entire "adaptive" layer — no
LLM, fully testable — and it directly targets each learner's real weaknesses.

---

## 9. Placement diagnostic

- `GetPlacement` returns a fixed-length diagnostic (e.g. 24 items) drawn from `placement.json`,
  spanning levels A2..C1 in a **deterministic** order (no answers sent to client).
- `GradePlacement({answers})` grades deterministically and estimates a level with a simple,
  documented rule: the **highest level at which the learner answers ≥70% of that level's items
  correctly**, defaulting to A1 if none. It sets `LearnerProfile.placement_level` and seeds the
  recommended-next pointer (`current_module_id`, §7) to the first `available` module of that
  level in `curriculum.json`. This is only a starting suggestion — the learner may open any
  module from the map regardless.
- Re-takeable; taking it again re-points `current_module_id` but never deletes existing
  `ModuleProgress` (so prior completions stand).
- Rationale for keeping it fixed/deterministic: reproducibility + testability (Prove-it).
  An adaptive/IRT placement is explicitly roadmap.

---

## 10. The daily "Today" session (the orchestrator)

`BuildTodaySession(profile, now)` assembles a deterministic ordered plan — the app's primary
screen and the embodiment of "an easy walk with real results":

1. **Warm up — due reviews** (interleaved vocab cards + skill items). **No artificial cap** —
   the queue is naturally bounded by what FSRS has scheduled as due. Spaced repetition first,
   while fresh.
2. **Learn — the recommended module**: if its lesson is unread → *Read lesson*; else →
   *Take quiz*. This is a **suggestion for one gradual step**, not a limit — the learner may
   study more, or open a different module from the map at any time (free navigation, §7).
3. **Produce — one output task**: a sentence-practice prompt on a recent module word, **or**
   a short interview turn on the module's linked interview topic (interleaving + output +
   corrective feedback). Uses existing pillars; if the LLM is disabled, falls back to a
   self-checked prompt and never blocks.
   **Phase note:** the module→vocab/interview links arrive in Phase 5. Until then (Phase 4),
   the Produce step uses a simple fallback — a sentence prompt on the most recently reviewed
   vocab card, or is omitted if none — and is enriched with per-module linkage in Phase 5.
4. **Focus — up to 3 leeches** (§8.4), if any.

The response is a typed list of **steps**, each a discriminated union
(`review | read_lesson | take_quiz | produce | focus`) carrying exactly the ids/payload the
front-end needs to render that step and deep-link to the relevant existing screen. The session
is **not persisted** — it is derived from current state on each request (stateless HTTP,
consistent with the base app). Completing steps mutates the underlying state (progress, FSRS),
so re-fetching `today` naturally advances the plan.

---

## 11. Integration with existing pillars

- **Vocabulary:** a module may declare `vocab` references resolved to existing deck sections
  (e.g. a B2 phrasal-verbs module points at the phrasal-verbs deck section). The *Produce*
  step and the module page can surface those words using the existing
  `GET /decks/{id}/cards?section=` and practice endpoints. No new vocab code — only linking.
- **Interview:** a module may declare an `interview_topic`. The *Produce* step can start an
  interview turn via the existing `ConductInterview` use case / interview endpoints, seeded
  with that topic. Reuse; do not fork the interview feature.
- **Sentence practice:** the *Produce* step reuses `CheckSentence` (LLM feedback) unchanged.

The Curriculum owns *linking metadata and orchestration*; it never reimplements a pillar.

---

## 12. API (FastAPI) — new endpoints

All bodies are Pydantic v2; validation at the boundary; domain errors mapped to status codes
via the existing `errors.py` pattern. New routers registered in `main.py`.

- `GET  /curriculum` → the map: levels → modules with `{id, title, level, track, status,
  quiz_best_score}` for the current learner.
- `GET  /curriculum/modules/{module_id}` → module detail (objectives, references, links,
  status, has_quiz).
- `GET  /curriculum/lessons/{module_id}` → `{ markdown, meta }` for the reader.
- `POST /curriculum/lessons/{module_id}/read` → marks the lesson read (idempotent);
  returns updated `ModuleProgress`.
- `GET  /curriculum/modules/{module_id}/quiz` → the quiz items **without** answers/explanations.
- `POST /curriculum/quiz/grade` → `{module_id, answers: [{item_id, given}]}` → per-item
  `{correct, explanation}` + `score`; updates `ModuleProgress`, upserts/schedules `SkillItem`s
  for failures, records `quiz_attempts`. Returns whether the module is now `completed` and the
  next module id.
- `GET  /placement` → diagnostic items (no answers).
- `POST /placement/grade` → `{answers}` → `{level, current_module_id}`; sets the profile.
- `GET  /session/today` → the ordered step list (§10).
- `GET  /review/skills/queue?limit=` → due skill items (prompt/example, no answer).
- `POST /review/skills` → `{skill_item_id, rating}` → new FSRS state (mirrors `POST /review`).
- `GET  /progress` → level roll-up: per level `{completed, total}` + overall A1→C2 percent +
  current streak (reuse existing streak from stats).

Pagination/limits on every list; `fsrs_due` indexed for the skill queue (no N+1 — batch the
`SkillItem` fetch by ids).

---

## 13. Content scope for THIS project (what the agent authors)

**Full A1→C2 content coverage is the end goal** — the manifest shows the complete ladder and
every level is meant to be authored. The critical distinction the owner should hold: **owning
the source books ≠ having the lessons.** Murphy/Hewings/…-in-Use are *raw material and a topic
skeleton*; each lesson (original prose) and each quiz (re-worded items) still has to be
**authored** file by file. That authoring — not the code — is the bulk of the total effort, and
it is done incrementally as data-only additions (in owner+assistant content sessions, like the
existing cheat sheets, and/or by the agent), guarded by the content-bundle test. Nothing about
having the books lets us skip the writing.

The engine must be **fully general** (loads any content matching §6). Because authoring all six
levels at once is large, the **code** ships first with a **vertical slice** of real content —
enough to exercise the whole loop end to end and be genuinely useful for the owner's B2→C1
goal — while the remaining levels are filled in behind the same schema (§16 Phase 6):

**Required initial content (author as files):**
- **Grammar track, B1→C1**: ≥ 12 modules following the Murphy(blue)/Hewings topic skeleton
  (e.g. dependent prepositions, perfect/continuous aspect, conditionals & wish, inversion,
  cleft sentences, participle clauses, articles, reported speech, modality of deduction,
  relative clauses, discourse markers, hedging/register).
- **Prepositions & word order**: 2 modules (these map directly to the owner's existing
  cheat-sheet material — reuse that content, re-authored into lessons).
- **Phrasal verbs**: 3 modules from *A Good Turn of Phrase* (business/work, communication,
  problem-solving), each with quiz items derived (re-worded) from that book's tests.
- **Collocations/idioms (C1)**: 2 modules from *…in Use: Advanced*.
- **Business English (C1)**: 1 module (register for technical interviews).
- **Placement**: ≥ 24 items spanning A2→C1.

Each module needs a lesson + ≥ 6 quiz items across ≥ 2 types. Levels not covered by the initial
slice (A1/A2 and C2) are listed in the manifest with `status: "authoring"` (§6.1) so the full
A1→C2 ladder is visible immediately, then authored as pure data adds toward full coverage —
no engine changes, each addition guarded by the content-bundle test.

> The books are a **topic and exercise skeleton**. Lessons are written in original words; quiz
> items are re-worded, not copied. Do not embed or ship the copyrighted PDFs. (The scanned
> English File PDFs cannot be text-extracted anyway and are for the owner's private reference.)

---

## 14. Error handling

- Validation → 422 (Pydantic). Unknown module/lesson/quiz id → a typed `CurriculumNotFound` →
  404. Grading an item with a malformed `given` → 422.
- LLM-graded items: provider failure must **not** fail the request — fall back to the
  deterministic result and mark the item `self_check` in the response. `NullProvider` never
  raises (base-spec rule).
- Content that fails validation at startup is a **hard boot error** (fail fast, never serve a
  broken curriculum) — surfaced in logs; the content-bundle test prevents shipping it.

---

## 15. Testing (evidence over assertion — CONTRIBUTING §4)

- **Domain unit tests:** `grade()` for every item type incl. normalisation edge cases;
  placement scoring rule; module-completion/advancement rule; leech detection; SkillItem
  review transitions. No IO.
- **Use-case tests:** with in-memory fakes for all new ports (fake `CurriculumContent`, fake
  repos, `NullProvider`, fake `Scheduler`). Cover: grade→skill-item upsert on failure, mark
  read, placement→profile, `BuildTodaySession` orderings (empty queue, unread lesson vs quiz
  due, leeches present).
- **Content-bundle test:** §6.5.
- **HTTP tests:** httpx `AsyncClient` for each new endpoint incl. 404/422 paths.
- **Frontend:** Vitest + Testing Library for `quiz-runner` (grading UI, per-item feedback),
  `lesson-reader`, `today` plan rendering, with a mocked client; MSW where needed.
- **E2E (Playwright, `NullProvider`):** placement → land on Today → open current module → read
  lesson → take quiz → a failed item appears in the skills review queue. One happy path.
- All gates green (Ruff, mypy strict, import-linter, Biome, tsc, Steiger, Vitest, Playwright,
  vite build) before any "done" claim.

---

## 16. Phased delivery (milestones — one spec, incremental build)

Each phase is independently shippable, fully typed, tested, and boundary-clean. Ship in order.

- **Phase 0 — Read the rules (delivers the owner's literal first ask).**
  Content model + loader + validator; `curriculum.json` + the vertical-slice **lessons**
  (no quizzes yet); `CurriculumContent` port + `FileCurriculumRepository`; `GetCurriculumMap`,
  `GetModule`, `GetLesson`, `MarkLessonRead`; `learner_profile` + `module_progress` tables;
  `/curriculum`, `/curriculum/modules/{id}`, `/curriculum/lessons/{id}`, `/…/read`;
  frontend `learn` + `lesson` pages, `curriculum-map` + `lesson-reader` widgets, `curriculum`
  entity, sanitized markdown renderer. **Outcome:** a readable, navigable A1→C2 map with real
  B1→C1 lessons and read-tracking.

- **Phase 1 — Retrieval practice.**
  `quiz.py` domain grade + item types; quiz JSON authored for the slice; `GetModuleQuiz`,
  `GradeQuiz` (deterministic only), `quiz_attempts` table; `/…/quiz`, `/quiz/grade`;
  `quiz-runner` widget (keyboard-first, §5.4) + `take-quiz` feature; completion rule (lesson
  read + quiz attempted, **no threshold**, §7) and recomputed recommended-next; free navigation
  across the map. **Outcome:** read → quiz → module completes; progress advances; the learner
  can jump anywhere.

- **Phase 2 — Spaced repetition of skills.**
  `SkillItem` aggregate + table + repo; `GradeQuiz` upserts skill items on failure;
  `GetSkillReviewQueue`/`RecordSkillReview` via the reused `Scheduler`; `review-skills`
  feature + `skill-item` entity; leech detection. **Outcome:** wrong answers resurface on an
  FSRS schedule; a Focus list exists.

- **Phase 3 — Placement.**
  `placement.json`; `GetPlacement`/`GradePlacement`; `/placement*`; `placement` page +
  feature; onboarding routes a new learner through placement first. **Outcome:** learners
  start at the right level.

- **Phase 4 — Today session.**
  `BuildTodaySession`; `/session/today`; `today` page + `daily-plan` widget; make Today the
  post-onboarding landing. Interleaves reviews + lesson/quiz + one produce step + focus.
  **Outcome:** one screen, one clear next action, every day.

- **Phase 5 — Pillar links + progress dashboard.**
  Module `vocab`/`interview_topic` links resolved into the Produce step and module page;
  `/progress` roll-up + `progress` entity + A1→C2 progress UI. **Outcome:** the four pillars
  read as one system; visible path to C2.

- **Phase 6 — Content fill (data only).**
  Author remaining slice modules to the §13 target and expand toward A1/A2/C2 as pure data
  adds. No engine changes; the content-bundle test guards each addition.

---

## 17. Risks & mitigations

- **Content volume dwarfs code.** Mitigation: engine is general; §13 defines a bounded initial
  slice; A1/A2/C2 are explicit stubs. Do not let content authoring block engine phases.
- **Copyright.** Mitigation: original lessons, re-worded items, no PDFs shipped (§13).
- **Over-reach into an adaptive/LLM path.** Mitigation: linear + deterministic is the spec;
  adaptivity is only leech-surfacing; LLM is optional with offline fallback. Anything more is a
  spec deviation → stop and flag.
- **Duplicating FSRS.** Mitigation: reuse the `Scheduler` port and `FsrsState`/`Rating`;
  `SkillItem` only adds a new persistence shape.
- **Boundary creep.** Mitigation: new packages added to import-linter/Steiger contracts in the
  same PR that introduces them.

---

## 18. Decisions & remaining questions

**Resolved by the owner (2026-08-16) — build to these:**
1. **No gates.** Free navigation; no completion threshold; no daily caps. Study is gradual by
   *presentation* only. (§7, §10)
2. **Full A1→C2 coverage is the goal**, authored incrementally; the manifest shows the whole
   ladder and not-yet-authored modules use `status: "authoring"` — no permanent "coming soon".
   (§6.1, §13)
3. **Landing page:** **Today** becomes the post-onboarding landing.
4. **Progress is always shown** (level roll-up + A1→C2 bar, §12 `/progress`).

**Still open (sensible defaults assumed; override anytime):**
- **A. Content-authoring ownership & sequencing (the one real fork).** The *engine* is a bounded
  code deliverable; authoring the *full A1→C2 lessons/quizzes* is the large, ongoing part.
  Default: **agent ships engine + the §13 B1→C1 slice first**, then A1/A2/C2 are authored as
  data-only additions (owner+assistant sessions and/or agent), so you get a working, useful app
  fast rather than waiting on all six levels. Override if you'd rather the agent author **all**
  levels before first ship (much longer to first usable build).
- **B. Interview linkage depth (Phase 5):** a single seeded topic per module (assumed) vs.
  per-module custom prompts.

---

## 19. Handoff notes for the implementing agent

- Obey `CONTRIBUTING.md` and this spec; if they conflict, **stop and flag** — do not improvise.
- Build **phase by phase** (§16); each phase ends with all CI gates green and observed, and a
  short note of what was run. No placeholders, no TODOs in committed code.
- **Regenerate the typed OpenAPI client** after each API change; the web app must consume the
  generated client only.
- Add every new backend package to the **import-linter** contracts and every new FSD slice to
  the **Steiger** config in the same phase that introduces it.
- Keep the domain pure: no FastAPI/SQLModel/httpx/py-fsrs imports under `domain/curriculum/**`.
- Reuse existing pillars (vocab, interview, sentence practice, FSRS scheduler) — link, don't
  fork. When unsure whether something is reuse vs. new, prefer reuse and flag.
- Commit style: Conventional Commits, no assistant/tool attribution.
```
