# Vocab Trainer Web

React 19 + Feature-Sliced Design frontend for the Vocab Trainer.

## Run

```bash
pnpm install
pnpm dev            # http://localhost:5173 (proxies /api → http://localhost:8000)
```

## Regenerate the API client

```bash
cd ../api && uv run python -c "import json; from vocab_api.main import create_app; print(json.dumps(create_app().openapi()))" > ../web/openapi.json
cd ../web && pnpm gen:api
```

## Checks

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm fsd && pnpm build && pnpm exec playwright test
```

The e2e suite (`tests/e2e`) runs the Vite dev server with `VITE_ENABLE_MSW=true`,
which starts an MSW browser worker (`src/shared/test/browser.ts`) serving the
same canned handlers used in Vitest — no backend required. That flag is
dev/e2e-only: a normal `pnpm dev` or production build never starts the worker.

## Layers (FSD)

`app → pages → widgets → features → entities → shared` — imports flow downward only.
