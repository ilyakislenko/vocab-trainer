# Vocab Trainer API

Hexagonal + DDD FastAPI backend for the Vocab Trainer.

## Run

```bash
cd apps/api
uv sync --dev
uv run uvicorn vocab_api.main:app --reload
```

On startup the API idempotently creates the default **Britlex English** deck
(~9800 words from `vocab_api/seed/data/`) unless a deck with that name already
exists. Words are tagged with the **section** of the source PDF file they came
from (`main`, `international`, `elementary`). Disable with
`VOCAB_SEED_DEFAULT_DECK=false`. Regenerate the data files from the source PDF
via `tools/britlex_pdf_to_markdown.py -o apps/api/src/vocab_api/seed/data`.

> Note: if you upgrade an existing database, the `section` column is added by
> migration but already-imported words keep `section = NULL` (the seeder is
> idempotent and won't re-tag them). Delete `vocab.db` once to re-seed with
> sections.

## Checks

```bash
uv run ruff check .
uv run mypy
uv run lint-imports
uv run pytest -q
```

## Layout

- `domain/` — framework-free entities and value objects
- `application/` — use cases + ports
- `infrastructure/` — SQLModel, py-fsrs, clock adapters
- `interfaces/http/` — FastAPI routers
- `config/` — settings + composition root
