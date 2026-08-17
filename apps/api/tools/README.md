# Content tooling

Offline dev tools for authoring curriculum content. Nothing here ships in the
app — these scripts are run by the owner on their machine and produce **data
adds** that still go through the normal content-bundle validation and review.

## `generate_quiz_items.py` — LLM-assisted item drafting

Drafts candidate quiz items for one module from a short **skeleton note** plus
the module's declared skills (read from the lesson frontmatter). The model is
told to re-word and vary structures; copyrighted exercise text is **never** fed
in, and the tool never writes to a live quiz.

```sh
uv run python tools/generate_quiz_items.py \
    --module a2.grammar.past-simple \
    --types mcq cloze word_order \
    --count 8 \
    --skeleton "past simple: regular and irregular forms, yes/no questions, negatives"
```

- **Input.** `--module` (id in `curriculum.json`), `--types` (any of
  `mcq cloze transform error_correction word_order listening`),
  `--count`, and `--skeleton` — the topic outline / structures to cover, in
  the owner's own words.
- **Provider.** Talks to the same OpenAI-compatible endpoint the app uses
  (`VOCAB_LLM_BASE_URL`, `VOCAB_LLM_MODEL`, `VOCAB_LLM_API_KEY`).
- **Output.** `src/vocab_api/seed/content/quizzes/<module>.draft.json` — never
  the live quiz, and nothing is committed. Every item is validated against the
  module's declared skills and the loader's shape rules before being written;
  invalid or leaky items are dropped and reported.

### The review loop (non-negotiable)

1. Run the tool to get a `*.draft.json`.
2. **Review it as a human:** read every item, edit/cull, and re-word anything
   that resembles source material. LLM output is a draft, never final.
3. Merge the reviewed items into the module's live `quizzes/<module>.json`.
4. Delete the draft file.
5. Run the content-bundle test (`uv run pytest tests/infrastructure/test_curriculum_content.py`)
   — it enforces skill validity, prompt-leak and duplicate-prompt guards, and
   the per-module size/type minimums.

The tool assists; it never auto-publishes.