# Vocab Trainer API

Hexagonal + DDD FastAPI backend for the Vocab Trainer.

## Run

```bash
cd apps/api
uv sync --dev
uv run uvicorn vocab_api.main:app --reload
```

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
