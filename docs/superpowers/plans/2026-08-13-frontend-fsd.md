# Vocab Trainer — Plan 2: Frontend (FSD) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A React 19 single-page app, organized with Feature-Sliced Design, that drives the existing backend: pick/create a deck, import a word list (dry-run preview + commit), run an FSRS review session (reveal + 4 ratings + keyboard shortcuts), and view stats.

**Architecture:** Feature-Sliced Design (`app → pages → widgets → features → entities → shared`, imports flow downward only, slices exposed via `index.ts`). Data access is TanStack Query over a **typed `openapi-fetch` client generated from the backend's OpenAPI schema**. Entities own read-queries for their data; features own the write-actions (mutations). Tests mock the network with MSW so the frontend builds and tests independently of a running backend.

**Tech Stack:** pnpm, Vite, React 19 + TypeScript (strict), Tailwind + shadcn/ui, TanStack Query v5, `openapi-fetch` + `openapi-typescript`, MSW v2, Vitest + Testing Library + jsdom, Playwright, Biome, Steiger (FSD boundary lint).

## Global Constraints

- **Node**: use the repo's pnpm; all web work under `apps/web/`. Run web commands from `apps/web/`.
- **FSD is law** (see `CONTRIBUTING.md`): imports flow strictly downward `app → pages → widgets → features → entities → shared`; no same-layer (cross-slice) imports; every slice is imported only through its `index.ts` public API. Enforced by Steiger (Task 12).
- **Types:** `tsc --noEmit` with `strict: true` passes; no `any`, no non-null `!` to dodge the checker, no `@ts-expect-error` without a one-line reason.
- **Quality:** no `TODO`/placeholder/dead code committed. YAGNI. Business/data logic lives in `features`/`entities` model segments, never inside a shared UI primitive.
- **API contract (from Plan 1 backend — do not invent endpoints):**
  - `POST /decks` `{name}` → `DeckOut {id,name}`
  - `GET /decks` → `DeckOut[]`
  - `POST /decks/{deck_id}/import` `{raw, format:"csv"|"markdown", dry_run}` → `ImportOut {committed, imported: CardOut[], errors: RowErrorOut[]}`
  - `GET /review/queue?deck_id=&limit=` → `CardOut[]`
  - `POST /review` `{card_id, rating:1|2|3|4}` → `CardOut`
  - `GET /stats?deck_id=` → `StatsOut {due_today, total_reviews}`
  - `CardOut = {id:number|null, word, translation, transcription:string|null}`.
- **API base URL:** the client's `baseUrl` is `import.meta.env.VITE_API_BASE_URL ?? "/api"`. Dev uses a Vite proxy (`/api` → `http://localhost:8000`, path rewritten to strip `/api`). MSW handlers therefore mock `"/api/..."` paths.
- **Commits:** Conventional Commits; **no assistant/tool attribution** in messages or code.

---

## File Structure

```
apps/web/
  package.json  vite.config.ts  tsconfig.json  biome.json  components.json  index.html
  playwright.config.ts  steiger.config.ts  vitest.setup.ts
  openapi.json                      # exported from backend (committed)
  .env.example
  src/
    main.tsx                        # ReactDOM root → <App/>
    app/
      App.tsx                       # providers + router shell
      providers.tsx                 # QueryClientProvider + theme
      router.tsx                    # routes
      index.css                     # tailwind + shadcn tokens
    pages/
      review/                       # ReviewPage
      import/                       # ImportPage
      stats/                        # StatsPage
    widgets/
      review-session/               # ReviewSession
      import-panel/                 # ImportPanel
      stats-panel/                  # StatsPanel
    features/
      select-deck/                  # DeckPicker + (choose/create)
      import-words/                 # ImportForm + useImportWords
      rate-card/                    # RatingBar + useRecordReview
    entities/
      deck/                         # model (queries) + ui (DeckSelect)
      card/                         # model (types, reviewKeys, useReviewQueue) + ui (CardFace)
      stats/                        # model (useStats)
    shared/
      api/                          # schema.d.ts (generated), client.ts, types.ts, index.ts
      test/                         # msw handlers, server, render helper
      ui/                           # shadcn components (button, card, input, ...)
      lib/                          # utils (cn)
      config/                       # constants
  tests/e2e/                        # Playwright specs
```

Each slice has an `index.ts` public API. Segments inside a slice: `ui/`, `model/`, `lib/`.

---

### Task 1: Scaffold web app + tooling

**Files:**
- Create: `apps/web/` project (Vite React-TS), `apps/web/biome.json`, `apps/web/vitest.setup.ts`, `apps/web/vite.config.ts` (edit), `apps/web/src/shared/lib/utils.ts`, `apps/web/src/app/index.css`, `apps/web/tests/smoke/app.test.tsx`; edit `.github/workflows/ci.yml` (add `web` job).

**Interfaces:**
- Produces: a Vite dev server, `pnpm test`/`pnpm build`/`pnpm typecheck`/`pnpm lint` scripts, Tailwind+shadcn configured, the FSD `src/` folders, and a passing smoke test.

- [ ] **Step 1: Scaffold and install**

Run from repo root:
```bash
pnpm create vite@latest apps/web -- --template react-ts
cd apps/web
pnpm install
pnpm add @tanstack/react-query openapi-fetch react-router-dom
pnpm add -D @biomejs/biome vitest @vitest/coverage-v8 jsdom \
  @testing-library/react @testing-library/user-event @testing-library/jest-dom \
  msw openapi-typescript steiger @feature-sliced/steiger-plugin \
  tailwindcss @tailwindcss/vite
pnpm dlx shadcn@latest init   # choose defaults; sets up components.json, path alias @/, index.css tokens
```
Follow shadcn's Vite guide: set the `@/*` path alias in `tsconfig.json` + `vite.config.ts` (`resolve.alias`), and Tailwind via `@tailwindcss/vite`. Move shadcn's generated CSS to `src/app/index.css` and import it from `src/main.tsx`.

**Point shadcn at the FSD layout** — edit `components.json` `aliases` so primitives land in `shared/`, otherwise the plan's `@/shared/ui/*` imports won't resolve:
```json
{
  "aliases": {
    "components": "@/shared",
    "ui": "@/shared/ui",
    "lib": "@/shared/lib",
    "utils": "@/shared/lib/utils",
    "hooks": "@/shared/lib"
  }
}
```
After this, `pnpm dlx shadcn@latest add button` writes `src/shared/ui/button.tsx` (importable as `@/shared/ui/button`) and its `cn` import resolves to `@/shared/lib/utils`.

- [ ] **Step 2: Configure scripts, tooling, and FSD folders**

`apps/web/package.json` scripts:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "lint": "biome check .",
    "gen:api": "openapi-typescript ./openapi.json -o ./src/shared/api/schema.d.ts"
  }
}
```
`apps/web/biome.json`:
```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "files": { "ignore": ["src/shared/api/schema.d.ts", "dist", "coverage"] },
  "linter": { "enabled": true, "rules": { "recommended": true } },
  "formatter": { "enabled": true, "indentStyle": "space", "lineWidth": 100 }
}
```
`apps/web/vite.config.ts` — add the dev proxy and vitest config:
```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
  test: { environment: "jsdom", globals: true, setupFiles: ["./vitest.setup.ts"] },
});
```
Create empty FSD dirs with a `.gitkeep` or the first `index.ts` as they're needed. Create `src/shared/lib/utils.ts` if shadcn didn't (the `cn` helper).

- [ ] **Step 3: Write the failing smoke test**

`apps/web/vitest.setup.ts`:
```ts
import "@testing-library/jest-dom/vitest";
```
`apps/web/tests/smoke/app.test.tsx`:
```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

function AppTitle() {
  return <h1>Vocab Trainer</h1>;
}

describe("smoke", () => {
  it("renders a heading", () => {
    render(<AppTitle />);
    expect(screen.getByRole("heading", { name: "Vocab Trainer" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 4: Run the test to verify it passes and the toolchain works**

Run:
```bash
pnpm test
pnpm typecheck
pnpm lint
pnpm build
```
Expected: vitest 1 passed; tsc clean; biome clean; build succeeds.

- [ ] **Step 5: Add the CI web job**

Edit `.github/workflows/ci.yml` — add a `web` job:
```yaml
  web:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/web
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm, cache-dependency-path: apps/web/pnpm-lock.yaml }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm typecheck
      - run: pnpm test
      - run: pnpm build
```

- [ ] **Step 6: Commit**

```bash
git add apps/web .github/workflows/ci.yml
git commit -m "feat(web): scaffold Vite + React 19 + FSD toolchain"
```

---

### Task 2: `shared/api` — typed client from the backend OpenAPI schema

**Files:**
- Create: `apps/web/openapi.json` (exported), `apps/web/src/shared/api/schema.d.ts` (generated), `apps/web/src/shared/api/client.ts`, `apps/web/src/shared/api/types.ts`, `apps/web/src/shared/api/index.ts`, `apps/web/src/shared/api/client.test.ts`, `apps/web/.env.example`

**Interfaces:**
- Produces:
  - `apiClient` — `createClient<paths>({ baseUrl })` from `openapi-fetch`.
  - `types.ts` re-exports: `Deck = components["schemas"]["DeckOut"]`, `Card = components["schemas"]["CardOut"]`, `Stats = components["schemas"]["StatsOut"]`, `ImportResult = components["schemas"]["ImportOut"]`, `RowError = components["schemas"]["RowErrorOut"]`, `ImportFormat = "csv" | "markdown"`, `Rating = 1 | 2 | 3 | 4`.
  - `shared/api/index.ts` exports `apiClient` and all types.

- [ ] **Step 1: Export the backend OpenAPI schema and generate types**

Run from repo root:
```bash
cd apps/api
uv run python -c "import json; from vocab_api.main import create_app; print(json.dumps(create_app().openapi(), indent=2))" > ../web/openapi.json
cd ../web
pnpm gen:api   # writes src/shared/api/schema.d.ts
```
Both `openapi.json` and `schema.d.ts` are committed (so the web app builds without the backend). Document the regenerate command in the web README later.

- [ ] **Step 2: Write the client, types, and a failing test**

`apps/web/src/shared/api/client.ts`:
```ts
import createClient from "openapi-fetch";
import type { paths } from "./schema";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const apiClient = createClient<paths>({ baseUrl });
```
`apps/web/src/shared/api/types.ts`:
```ts
import type { components } from "./schema";

export type Deck = components["schemas"]["DeckOut"];
export type Card = components["schemas"]["CardOut"];
export type Stats = components["schemas"]["StatsOut"];
export type ImportResult = components["schemas"]["ImportOut"];
export type RowError = components["schemas"]["RowErrorOut"];
export type ImportFormat = "csv" | "markdown";
export type Rating = 1 | 2 | 3 | 4;
```
`apps/web/src/shared/api/index.ts`:
```ts
export { apiClient } from "./client";
export type { Deck, Card, Stats, ImportResult, RowError, ImportFormat, Rating } from "./types";
```
`apps/web/src/shared/api/client.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { apiClient } from "./client";

describe("apiClient", () => {
  it("exposes typed GET and POST methods", () => {
    expect(typeof apiClient.GET).toBe("function");
    expect(typeof apiClient.POST).toBe("function");
  });
});
```

- [ ] **Step 3: Run the test**

Run: `pnpm test src/shared/api/client.test.ts` → PASS; `pnpm typecheck` → clean (proves `paths`/`components` types generated correctly).

- [ ] **Step 4: Add `.env.example`**

`apps/web/.env.example`:
```dotenv
# Leave unset to use the Vite dev proxy at /api; set for a direct backend origin.
VITE_API_BASE_URL=/api
```

- [ ] **Step 5: Commit**

```bash
git add apps/web/openapi.json apps/web/src/shared/api apps/web/.env.example
git commit -m "feat(web): add typed api client generated from backend OpenAPI"
```

---

### Task 3: `shared/test` — MSW mocking infra + render helper

**Files:**
- Create: `apps/web/src/shared/test/handlers.ts`, `apps/web/src/shared/test/server.ts`, `apps/web/src/shared/test/render.tsx`, `apps/web/src/shared/test/index.ts`, `apps/web/src/shared/test/handlers.test.ts`; edit `apps/web/vitest.setup.ts`

**Interfaces:**
- Produces:
  - `handlers` — default MSW handlers for `/api/decks` (GET/POST), `/api/decks/:id/import` (POST), `/api/review/queue` (GET), `/api/review` (POST), `/api/stats` (GET).
  - `server` — `setupServer(...handlers)`.
  - `renderWithProviders(ui)` — renders inside a fresh `QueryClientProvider` (retry disabled).
- `vitest.setup.ts` starts/stops the server and resets handlers per test. Later tasks override specific handlers with `server.use(...)`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/shared/test/handlers.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { apiClient } from "@/shared/api";

describe("msw handlers", () => {
  it("intercepts GET /decks with the default handler", async () => {
    const { data } = await apiClient.GET("/decks");
    expect(data).toEqual([{ id: 1, name: "Sample" }]);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/shared/test/handlers.test.ts`
Expected: FAIL — request not intercepted (no MSW yet), `data` is undefined / network error.

- [ ] **Step 3: Implement handlers, server, render helper, and wire setup**

`apps/web/src/shared/test/handlers.ts`:
```ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/decks", () => HttpResponse.json([{ id: 1, name: "Sample" }])),
  http.post("/api/decks", async ({ request }) => {
    const body = (await request.json()) as { name: string };
    return HttpResponse.json({ id: 2, name: body.name });
  }),
  http.post("/api/decks/:id/import", () =>
    HttpResponse.json({ committed: false, imported: [], errors: [] })),
  http.get("/api/review/queue", () => HttpResponse.json([])),
  http.post("/api/review", async ({ request }) => {
    const body = (await request.json()) as { card_id: number };
    return HttpResponse.json({
      id: body.card_id, word: "run", translation: "бежать", transcription: null,
    });
  }),
  http.get("/api/stats", () => HttpResponse.json({ due_today: 0, total_reviews: 0 })),
];
```
`apps/web/src/shared/test/server.ts`:
```ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```
`apps/web/src/shared/test/render.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";

export function renderWithProviders(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}
```
`apps/web/src/shared/test/index.ts`:
```ts
export { handlers } from "./handlers";
export { server } from "./server";
export { renderWithProviders } from "./render";
```
Edit `apps/web/vitest.setup.ts`:
```ts
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "@/shared/test/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pnpm test src/shared/test/handlers.test.ts` → PASS; then `pnpm test` (smoke + api + handlers all green).

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/shared/test apps/web/vitest.setup.ts
git commit -m "test(web): add MSW mocking infra and provider render helper"
```

---

### Task 4: `entities/deck` — queries + `DeckSelect`

**Files:**
- Create: `apps/web/src/entities/deck/model/queries.ts`, `apps/web/src/entities/deck/ui/DeckSelect.tsx`, `apps/web/src/entities/deck/index.ts`, `apps/web/src/entities/deck/model/queries.test.tsx`; add shadcn `select` + `button` via `pnpm dlx shadcn@latest add select button` if not present.

**Interfaces:**
- Consumes: `apiClient`, `Deck` from `@/shared/api`.
- Produces:
  - `deckKeys = { all: ["decks"] as const }`.
  - `useDecks()` → `UseQueryResult<Deck[]>` (GET /decks).
  - `useCreateDeck()` → mutation `(name: string) => Deck`, invalidates `deckKeys.all`.
  - `DeckSelect({ decks, value, onChange })` — a shadcn Select of deck names.

- [ ] **Step 1: Write the failing test**

`apps/web/src/entities/deck/model/queries.test.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useDecks } from "./queries";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useDecks", () => {
  it("loads decks from the api", async () => {
    const { result } = renderHook(() => useDecks(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: 1, name: "Sample" }]);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/entities/deck` → FAIL (module not found).

- [ ] **Step 3: Implement queries and UI**

`apps/web/src/entities/deck/model/queries.ts`:
```ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, type Deck } from "@/shared/api";

export const deckKeys = { all: ["decks"] as const };

export function useDecks() {
  return useQuery({
    queryKey: deckKeys.all,
    queryFn: async (): Promise<Deck[]> => {
      const { data, error } = await apiClient.GET("/decks");
      if (error) throw new Error("Failed to load decks");
      return data;
    },
  });
}

export function useCreateDeck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (name: string): Promise<Deck> => {
      const { data, error } = await apiClient.POST("/decks", { body: { name } });
      if (error) throw new Error("Failed to create deck");
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: deckKeys.all }),
  });
}
```
`apps/web/src/entities/deck/ui/DeckSelect.tsx`:
```tsx
import type { Deck } from "@/shared/api";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/shared/ui/select";

export function DeckSelect({
  decks, value, onChange,
}: { decks: Deck[]; value: number | null; onChange: (id: number) => void }) {
  return (
    <Select value={value ? String(value) : undefined} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger className="w-56"><SelectValue placeholder="Select a deck" /></SelectTrigger>
      <SelectContent>
        {decks.map((d) => (
          <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```
`apps/web/src/entities/deck/index.ts`:
```ts
export { deckKeys, useDecks, useCreateDeck } from "./model/queries";
export { DeckSelect } from "./ui/DeckSelect";
```
(Task 1 already pointed shadcn's `components.json` `aliases.ui` at `@/shared/ui`, so `pnpm dlx shadcn@latest add select button` writes to `src/shared/ui/` and the imports above resolve.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `pnpm test src/entities/deck` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/entities/deck apps/web/src/shared/ui apps/web/components.json
git commit -m "feat(web): add deck entity (queries + DeckSelect)"
```

---

### Task 5: `entities/card` — types, review queue query, `CardFace`

**Files:**
- Create: `apps/web/src/entities/card/model/queries.ts`, `apps/web/src/entities/card/ui/CardFace.tsx`, `apps/web/src/entities/card/index.ts`, `apps/web/src/entities/card/model/queries.test.tsx`; shadcn `card` via `pnpm dlx shadcn@latest add card`.

**Interfaces:**
- Consumes: `apiClient`, `Card` from `@/shared/api`.
- Produces:
  - `reviewKeys = { queue: (deckId: number) => ["review", "queue", deckId] as const }`.
  - `useReviewQueue(deckId: number | null, limit = 20)` → `UseQueryResult<Card[]>` (GET /review/queue; `enabled` only when `deckId` is set).
  - `CardFace({ card, revealed })` — shows the word always; transcription + translation only when `revealed`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/entities/card/model/queries.test.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/shared/test";
import { useReviewQueue } from "./queries";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useReviewQueue", () => {
  it("is disabled when no deck is selected", () => {
    const { result } = renderHook(() => useReviewQueue(null), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("loads due cards for a deck", async () => {
    server.use(
      http.get("/api/review/queue", () =>
        HttpResponse.json([{ id: 7, word: "run", translation: "бежать", transcription: "rʌn" }])),
    );
    const { result } = renderHook(() => useReviewQueue(1), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].word).toBe("run");
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/entities/card` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/entities/card/model/queries.ts`:
```ts
import { useQuery } from "@tanstack/react-query";
import { apiClient, type Card } from "@/shared/api";

export const reviewKeys = {
  queue: (deckId: number) => ["review", "queue", deckId] as const,
};

export function useReviewQueue(deckId: number | null, limit = 20) {
  return useQuery({
    queryKey: deckId === null ? ["review", "queue", "none"] : reviewKeys.queue(deckId),
    enabled: deckId !== null,
    queryFn: async (): Promise<Card[]> => {
      const { data, error } = await apiClient.GET("/review/queue", {
        params: { query: { deck_id: deckId as number, limit } },
      });
      if (error) throw new Error("Failed to load review queue");
      return data;
    },
  });
}
```
`apps/web/src/entities/card/ui/CardFace.tsx`:
```tsx
import type { Card } from "@/shared/api";
import { Card as UICard, CardContent } from "@/shared/ui/card";

export function CardFace({ card, revealed }: { card: Card; revealed: boolean }) {
  return (
    <UICard className="w-full max-w-md">
      <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
        <span className="text-3xl font-semibold">{card.word}</span>
        {revealed && (
          <>
            {card.transcription && <span className="text-muted-foreground">/{card.transcription}/</span>}
            <span className="text-xl">{card.translation}</span>
          </>
        )}
      </CardContent>
    </UICard>
  );
}
```
`apps/web/src/entities/card/index.ts`:
```ts
export { reviewKeys, useReviewQueue } from "./model/queries";
export { CardFace } from "./ui/CardFace";
```

- [ ] **Step 4: Run the test**

Run: `pnpm test src/entities/card` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/entities/card apps/web/src/shared/ui
git commit -m "feat(web): add card entity (review queue query + CardFace)"
```

---

### Task 6: `features/select-deck` — pick or create a deck

**Files:**
- Create: `apps/web/src/features/select-deck/ui/DeckPicker.tsx`, `apps/web/src/features/select-deck/index.ts`, `apps/web/src/features/select-deck/ui/DeckPicker.test.tsx`; shadcn `input` via `pnpm dlx shadcn@latest add input`.

**Interfaces:**
- Consumes: `useDecks`, `useCreateDeck`, `DeckSelect` from `@/entities/deck`; `Input`, `Button` from `@/shared/ui`.
- Produces: `DeckPicker({ value, onChange })` — renders the deck `DeckSelect` plus a create-deck input+button; on create success selects the new deck via `onChange`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/features/select-deck/ui/DeckPicker.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { DeckPicker } from "./DeckPicker";

describe("DeckPicker", () => {
  it("creates a deck and selects it", async () => {
    server.use(
      http.post("/api/decks", () => HttpResponse.json({ id: 9, name: "Travel" })),
    );
    const onChange = vi.fn();
    renderWithProviders(<DeckPicker value={null} onChange={onChange} />);
    await userEvent.type(screen.getByPlaceholderText(/new deck/i), "Travel");
    await userEvent.click(screen.getByRole("button", { name: /create/i }));
    await waitFor(() => expect(onChange).toHaveBeenCalledWith(9));
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/features/select-deck` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/features/select-deck/ui/DeckPicker.tsx`:
```tsx
import { useState } from "react";
import { DeckSelect, useCreateDeck, useDecks } from "@/entities/deck";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";

export function DeckPicker({
  value, onChange,
}: { value: number | null; onChange: (id: number) => void }) {
  const decks = useDecks();
  const createDeck = useCreateDeck();
  const [name, setName] = useState("");

  const handleCreate = async () => {
    if (!name.trim()) return;
    const deck = await createDeck.mutateAsync(name.trim());
    setName("");
    if (deck.id !== null) onChange(deck.id);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {decks.data && <DeckSelect decks={decks.data} value={value} onChange={onChange} />}
      <Input
        className="w-40" placeholder="New deck…" value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Button onClick={handleCreate} disabled={createDeck.isPending}>Create</Button>
    </div>
  );
}
```
`apps/web/src/features/select-deck/index.ts`:
```ts
export { DeckPicker } from "./ui/DeckPicker";
```

- [ ] **Step 4: Run the test**

Run: `pnpm test src/features/select-deck` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/select-deck apps/web/src/shared/ui
git commit -m "feat(web): add select-deck feature"
```

---

### Task 7: `features/import-words` — form + dry-run preview + commit

**Files:**
- Create: `apps/web/src/features/import-words/model/use-import-words.ts`, `apps/web/src/features/import-words/ui/ImportForm.tsx`, `apps/web/src/features/import-words/index.ts`, `apps/web/src/features/import-words/ui/ImportForm.test.tsx`; shadcn `textarea` via `pnpm dlx shadcn@latest add textarea`.

**Interfaces:**
- Consumes: `apiClient`, `ImportResult`, `ImportFormat` from `@/shared/api`.
- Produces:
  - `useImportWords(deckId)` → mutation `({raw, format, dryRun}) => ImportResult`; on a committed success invalidates review + stats queries.
  - `ImportForm({ deckId })` — textarea + format toggle (csv/markdown) + "Preview" (dry_run=true) and "Import" (dry_run=false) buttons; shows the returned imported-count and any row errors.

- [ ] **Step 1: Write the failing test**

`apps/web/src/features/import-words/ui/ImportForm.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ImportForm } from "./ImportForm";

describe("ImportForm", () => {
  it("previews without committing then imports", async () => {
    server.use(
      http.post("/api/decks/:id/import", async ({ request }) => {
        const body = (await request.json()) as { dry_run: boolean };
        return HttpResponse.json({
          committed: !body.dry_run,
          imported: [{ id: body.dry_run ? null : 1, word: "run", translation: "бежать", transcription: null }],
          errors: [],
        });
      }),
    );
    renderWithProviders(<ImportForm deckId={1} />);
    await userEvent.type(screen.getByRole("textbox"), "run,бежать");
    await userEvent.click(screen.getByRole("button", { name: /preview/i }));
    await waitFor(() => expect(screen.getByText(/1 word/i)).toBeInTheDocument());
    expect(screen.getByText(/preview/i)).toBeInTheDocument(); // not yet committed
    await userEvent.click(screen.getByRole("button", { name: /^import$/i }));
    await waitFor(() => expect(screen.getByText(/imported 1/i)).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/features/import-words` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/features/import-words/model/use-import-words.ts`:
```ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, type ImportFormat, type ImportResult } from "@/shared/api";

export function useImportWords(deckId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (
      input: { raw: string; format: ImportFormat; dryRun: boolean },
    ): Promise<ImportResult> => {
      const { data, error } = await apiClient.POST("/decks/{deck_id}/import", {
        params: { path: { deck_id: deckId } },
        body: { raw: input.raw, format: input.format, dry_run: input.dryRun },
      });
      if (error) throw new Error("Import failed");
      return data;
    },
    onSuccess: (result) => {
      if (result.committed) {
        qc.invalidateQueries({ queryKey: ["review", "queue", deckId] });
        qc.invalidateQueries({ queryKey: ["stats", deckId] });
      }
    },
  });
}
```
`apps/web/src/features/import-words/ui/ImportForm.tsx`:
```tsx
import { useState } from "react";
import type { ImportFormat } from "@/shared/api";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { useImportWords } from "../model/use-import-words";

export function ImportForm({ deckId }: { deckId: number }) {
  const [raw, setRaw] = useState("");
  const [format, setFormat] = useState<ImportFormat>("csv");
  const importWords = useImportWords(deckId);
  const result = importWords.data;

  const run = (dryRun: boolean) => importWords.mutate({ raw, format, dryRun });

  return (
    <div className="flex flex-col gap-3">
      <Textarea
        value={raw} onChange={(e) => setRaw(e.target.value)}
        placeholder="word,transcription,translation" rows={8}
      />
      <div className="flex items-center gap-2">
        <select
          aria-label="format" value={format}
          onChange={(e) => setFormat(e.target.value as ImportFormat)}
        >
          <option value="csv">CSV</option>
          <option value="markdown">Markdown</option>
        </select>
        <Button variant="secondary" onClick={() => run(true)} disabled={importWords.isPending}>
          Preview
        </Button>
        <Button onClick={() => run(false)} disabled={importWords.isPending}>Import</Button>
      </div>
      {result && (
        <div className="text-sm">
          <p>
            {result.committed
              ? `Imported ${result.imported.length}`
              : `Preview: ${result.imported.length} word(s)`}
          </p>
          {result.errors.length > 0 && (
            <ul className="text-destructive">
              {result.errors.map((e) => (
                <li key={e.line}>line {e.line}: {e.reason}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
```
`apps/web/src/features/import-words/index.ts`:
```ts
export { ImportForm } from "./ui/ImportForm";
export { useImportWords } from "./model/use-import-words";
```

- [ ] **Step 4: Run the test**

Run: `pnpm test src/features/import-words` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/import-words apps/web/src/shared/ui
git commit -m "feat(web): add import-words feature with preview and commit"
```

---

### Task 8: `features/rate-card` — rating bar + record-review mutation

**Files:**
- Create: `apps/web/src/features/rate-card/model/use-record-review.ts`, `apps/web/src/features/rate-card/ui/RatingBar.tsx`, `apps/web/src/features/rate-card/index.ts`, `apps/web/src/features/rate-card/ui/RatingBar.test.tsx`

**Interfaces:**
- Consumes: `apiClient`, `Card`, `Rating` from `@/shared/api`.
- Produces:
  - `useRecordReview(deckId)` → mutation `({cardId, rating}) => Card`; on success invalidates the deck's review queue + stats.
  - `RatingBar({ onRate, disabled })` — 4 buttons (Again/Hard/Good/Easy → 1/2/3/4) AND keyboard shortcuts (`1`–`4`) that call `onRate(rating)`. The keyboard listener is attached on mount and removed on unmount; it is a no-op while `disabled`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/features/rate-card/ui/RatingBar.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RatingBar } from "./RatingBar";

describe("RatingBar", () => {
  it("calls onRate from a button click", async () => {
    const onRate = vi.fn();
    render(<RatingBar onRate={onRate} disabled={false} />);
    await userEvent.click(screen.getByRole("button", { name: /good/i }));
    expect(onRate).toHaveBeenCalledWith(3);
  });

  it("calls onRate from a number key", async () => {
    const onRate = vi.fn();
    render(<RatingBar onRate={onRate} disabled={false} />);
    await userEvent.keyboard("4");
    expect(onRate).toHaveBeenCalledWith(4);
  });

  it("ignores keys when disabled", async () => {
    const onRate = vi.fn();
    render(<RatingBar onRate={onRate} disabled={true} />);
    await userEvent.keyboard("1");
    expect(onRate).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/features/rate-card` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/features/rate-card/model/use-record-review.ts`:
```ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, type Card, type Rating } from "@/shared/api";

export function useRecordReview(deckId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: { cardId: number; rating: Rating }): Promise<Card> => {
      const { data, error } = await apiClient.POST("/review", {
        body: { card_id: input.cardId, rating: input.rating },
      });
      if (error) throw new Error("Failed to record review");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["review", "queue", deckId] });
      qc.invalidateQueries({ queryKey: ["stats", deckId] });
    },
  });
}
```
`apps/web/src/features/rate-card/ui/RatingBar.tsx`:
```tsx
import { useEffect } from "react";
import type { Rating } from "@/shared/api";
import { Button } from "@/shared/ui/button";

const RATINGS: { rating: Rating; label: string }[] = [
  { rating: 1, label: "Again" }, { rating: 2, label: "Hard" },
  { rating: 3, label: "Good" }, { rating: 4, label: "Easy" },
];

export function RatingBar({
  onRate, disabled,
}: { onRate: (rating: Rating) => void; disabled: boolean }) {
  useEffect(() => {
    if (disabled) return;
    const handler = (e: KeyboardEvent) => {
      const rating = Number(e.key);
      if (rating >= 1 && rating <= 4) onRate(rating as Rating);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onRate, disabled]);

  return (
    <div className="flex gap-2">
      {RATINGS.map(({ rating, label }) => (
        <Button key={rating} variant="outline" disabled={disabled} onClick={() => onRate(rating)}>
          {label} <span className="ml-1 text-muted-foreground">{rating}</span>
        </Button>
      ))}
    </div>
  );
}
```
`apps/web/src/features/rate-card/index.ts`:
```ts
export { RatingBar } from "./ui/RatingBar";
export { useRecordReview } from "./model/use-record-review";
```

- [ ] **Step 4: Run the test**

Run: `pnpm test src/features/rate-card` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/rate-card
git commit -m "feat(web): add rate-card feature with keyboard shortcuts"
```

---

### Task 9: `widgets/review-session` — the review flow

**Files:**
- Create: `apps/web/src/widgets/review-session/ui/ReviewSession.tsx`, `apps/web/src/widgets/review-session/index.ts`, `apps/web/src/widgets/review-session/ui/ReviewSession.test.tsx`

**Interfaces:**
- Consumes: `useReviewQueue`, `CardFace` from `@/entities/card`; `RatingBar`, `useRecordReview` from `@/features/rate-card`; `Button` from `@/shared/ui`.
- Produces: `ReviewSession({ deckId })` — loads the queue; shows the current card via `CardFace` (hidden answer), a "Show answer" button that reveals it and enables `RatingBar`; on a rating it records the review and advances to the next card; shows a progress indicator (`n / total`) and a "You're all caught up" empty state when the queue is empty or exhausted.

- [ ] **Step 1: Write the failing test**

`apps/web/src/widgets/review-session/ui/ReviewSession.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ReviewSession } from "./ReviewSession";

describe("ReviewSession", () => {
  it("reveals, rates, advances, and finishes", async () => {
    server.use(
      http.get("/api/review/queue", () =>
        HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null },
          { id: 2, word: "jump", translation: "прыгать", transcription: null },
        ])),
      http.post("/api/review", async ({ request }) => {
        const b = (await request.json()) as { card_id: number };
        return HttpResponse.json({ id: b.card_id, word: "x", translation: "y", transcription: null });
      }),
    );
    renderWithProviders(<ReviewSession deckId={1} />);
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    expect(screen.queryByText("бежать")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show answer/i }));
    expect(screen.getByText("бежать")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /good/i }));
    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /show answer/i }));
    await userEvent.click(screen.getByRole("button", { name: /easy/i }));
    await waitFor(() => expect(screen.getByText(/caught up/i)).toBeInTheDocument());
  });

  it("shows the empty state when nothing is due", async () => {
    server.use(http.get("/api/review/queue", () => HttpResponse.json([])));
    renderWithProviders(<ReviewSession deckId={1} />);
    await waitFor(() => expect(screen.getByText(/caught up/i)).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/widgets/review-session` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/widgets/review-session/ui/ReviewSession.tsx`:
```tsx
import { useState } from "react";
import type { Rating } from "@/shared/api";
import { CardFace, useReviewQueue } from "@/entities/card";
import { RatingBar, useRecordReview } from "@/features/rate-card";
import { Button } from "@/shared/ui/button";

export function ReviewSession({ deckId }: { deckId: number }) {
  const queue = useReviewQueue(deckId);
  const record = useRecordReview(deckId);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);

  if (queue.isLoading) return <p>Loading…</p>;
  const cards = queue.data ?? [];
  const card = cards[index];

  if (!card) {
    return <p className="text-lg text-muted-foreground">You're all caught up 🎉</p>;
  }

  const rate = async (rating: Rating) => {
    if (card.id === null) return;
    await record.mutateAsync({ cardId: card.id, rating });
    setRevealed(false);
    setIndex((i) => i + 1);
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-sm text-muted-foreground">{index + 1} / {cards.length}</p>
      <CardFace card={card} revealed={revealed} />
      {revealed ? (
        <RatingBar onRate={rate} disabled={record.isPending} />
      ) : (
        <Button onClick={() => setRevealed(true)}>Show answer</Button>
      )}
    </div>
  );
}
```
`apps/web/src/widgets/review-session/index.ts`:
```ts
export { ReviewSession } from "./ui/ReviewSession";
```

- [ ] **Step 4: Run the test**

Run: `pnpm test src/widgets/review-session` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/widgets/review-session
git commit -m "feat(web): add review-session widget"
```

---

### Task 10: `widgets/import-panel` + `widgets/stats-panel` + `entities/stats`

**Files:**
- Create: `apps/web/src/entities/stats/model/queries.ts`, `apps/web/src/entities/stats/index.ts`, `apps/web/src/widgets/import-panel/ui/ImportPanel.tsx`, `apps/web/src/widgets/import-panel/index.ts`, `apps/web/src/widgets/stats-panel/ui/StatsPanel.tsx`, `apps/web/src/widgets/stats-panel/index.ts`, `apps/web/src/widgets/stats-panel/ui/StatsPanel.test.tsx`

**Interfaces:**
- Produces:
  - `entities/stats`: `statsKeys = { byDeck: (deckId: number) => ["stats", deckId] as const }`; `useStats(deckId: number | null)` → `UseQueryResult<Stats>` (GET /stats; enabled only when deck set).
  - `ImportPanel({ deckId })` — a titled wrapper around `<ImportForm deckId={deckId} />` from `@/features/import-words`.
  - `StatsPanel({ deckId })` — shows `due_today` and `total_reviews` from `useStats`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/widgets/stats-panel/ui/StatsPanel.test.tsx`:
```tsx
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { StatsPanel } from "./StatsPanel";

describe("StatsPanel", () => {
  it("shows due and reviewed counts", async () => {
    server.use(
      http.get("/api/stats", () => HttpResponse.json({ due_today: 5, total_reviews: 12 })),
    );
    renderWithProviders(<StatsPanel deckId={1} />);
    await waitFor(() => expect(screen.getByText("5")).toBeInTheDocument());
    expect(screen.getByText("12")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/widgets/stats-panel` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/entities/stats/model/queries.ts`:
```ts
import { useQuery } from "@tanstack/react-query";
import { apiClient, type Stats } from "@/shared/api";

export const statsKeys = { byDeck: (deckId: number) => ["stats", deckId] as const };

export function useStats(deckId: number | null) {
  return useQuery({
    queryKey: deckId === null ? ["stats", "none"] : statsKeys.byDeck(deckId),
    enabled: deckId !== null,
    queryFn: async (): Promise<Stats> => {
      const { data, error } = await apiClient.GET("/stats", {
        params: { query: { deck_id: deckId as number } },
      });
      if (error) throw new Error("Failed to load stats");
      return data;
    },
  });
}
```
`apps/web/src/entities/stats/index.ts`:
```ts
export { statsKeys, useStats } from "./model/queries";
```
`apps/web/src/widgets/import-panel/ui/ImportPanel.tsx`:
```tsx
import { ImportForm } from "@/features/import-words";

export function ImportPanel({ deckId }: { deckId: number }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-semibold">Import words</h2>
      <ImportForm deckId={deckId} />
    </section>
  );
}
```
`apps/web/src/widgets/import-panel/index.ts`:
```ts
export { ImportPanel } from "./ui/ImportPanel";
```
`apps/web/src/widgets/stats-panel/ui/StatsPanel.tsx`:
```tsx
import { useStats } from "@/entities/stats";
import { Card, CardContent } from "@/shared/ui/card";

function Tile({ label, value }: { label: string; value: number }) {
  return (
    <Card className="flex-1">
      <CardContent className="py-6 text-center">
        <div className="text-3xl font-semibold">{value}</div>
        <div className="text-sm text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}

export function StatsPanel({ deckId }: { deckId: number }) {
  const stats = useStats(deckId);
  if (!stats.data) return <p>Loading…</p>;
  return (
    <div className="flex gap-3">
      <Tile label="Due today" value={stats.data.due_today} />
      <Tile label="Total reviews" value={stats.data.total_reviews} />
    </div>
  );
}
```
`apps/web/src/widgets/stats-panel/index.ts`:
```ts
export { StatsPanel } from "./ui/StatsPanel";
```

- [ ] **Step 4: Run the test**

Run: `pnpm test src/widgets/stats-panel` → PASS; `pnpm typecheck` clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/entities/stats apps/web/src/widgets/import-panel apps/web/src/widgets/stats-panel
git commit -m "feat(web): add stats entity + import/stats panels"
```

---

### Task 11: `app` + `pages` — providers, router, nav shell

**Files:**
- Create: `apps/web/src/app/providers.tsx`, `apps/web/src/app/router.tsx`, `apps/web/src/app/App.tsx`, `apps/web/src/app/index.ts`, `apps/web/src/pages/review/ui/ReviewPage.tsx`, `apps/web/src/pages/review/index.ts`, `apps/web/src/pages/import/ui/ImportPage.tsx`, `apps/web/src/pages/import/index.ts`, `apps/web/src/pages/stats/ui/StatsPage.tsx`, `apps/web/src/pages/stats/index.ts`, `apps/web/src/app/App.test.tsx`; edit `apps/web/src/main.tsx`.

**Interfaces:**
- Produces:
  - `Providers({ children })` — wraps in one `QueryClientProvider` (module-level `QueryClient`).
  - Router with routes `/` (Review), `/import`, `/stats`, and a shared nav that also hosts the `DeckPicker` (selected deck id held in `App` state and passed to pages).
  - `App` — the composed shell. `main.tsx` renders `<App/>`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/app/App.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the review page by default and navigates to import", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: /vocab trainer/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: /import/i }));
    await waitFor(() => expect(screen.getByText(/import words/i)).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `pnpm test src/app` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/app/providers.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const queryClient = new QueryClient();

export function Providers({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```
`apps/web/src/pages/review/ui/ReviewPage.tsx`:
```tsx
import { ReviewSession } from "@/widgets/review-session";

export function ReviewPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck to start.</p>;
  return <ReviewSession deckId={deckId} />;
}
```
`apps/web/src/pages/review/index.ts`: `export { ReviewPage } from "./ui/ReviewPage";`
`apps/web/src/pages/import/ui/ImportPage.tsx`:
```tsx
import { ImportPanel } from "@/widgets/import-panel";

export function ImportPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck first.</p>;
  return <ImportPanel deckId={deckId} />;
}
```
`apps/web/src/pages/import/index.ts`: `export { ImportPage } from "./ui/ImportPage";`
`apps/web/src/pages/stats/ui/StatsPage.tsx`:
```tsx
import { StatsPanel } from "@/widgets/stats-panel";

export function StatsPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck first.</p>;
  return <StatsPanel deckId={deckId} />;
}
```
`apps/web/src/pages/stats/index.ts`: `export { StatsPage } from "./ui/StatsPage";`
`apps/web/src/app/App.tsx`:
```tsx
import { useState } from "react";
import { Link, MemoryRouter, Route, Routes } from "react-router-dom";
import { DeckPicker } from "@/features/select-deck";
import { ImportPage } from "@/pages/import";
import { ReviewPage } from "@/pages/review";
import { StatsPage } from "@/pages/stats";
import { Providers } from "./providers";

export function App() {
  const [deckId, setDeckId] = useState<number | null>(null);
  return (
    <Providers>
      <MemoryRouter>
        <header className="flex flex-wrap items-center justify-between gap-4 border-b p-4">
          <h1 className="text-xl font-bold">Vocab Trainer</h1>
          <nav className="flex gap-4">
            <Link to="/">Review</Link>
            <Link to="/import">Import</Link>
            <Link to="/stats">Stats</Link>
          </nav>
          <DeckPicker value={deckId} onChange={setDeckId} />
        </header>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<ReviewPage deckId={deckId} />} />
            <Route path="/import" element={<ImportPage deckId={deckId} />} />
            <Route path="/stats" element={<StatsPage deckId={deckId} />} />
          </Routes>
        </main>
      </MemoryRouter>
    </Providers>
  );
}
```
(Use `MemoryRouter` in `App` for testability; if you prefer `BrowserRouter` for the real app, split a router-less `App` from an entry that wraps it — but `MemoryRouter` works in the browser too for this SPA. Keep the test green.)
`apps/web/src/app/index.ts`: `export { App } from "./App";`
Edit `apps/web/src/main.tsx`:
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app";
import "./app/index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode><App /></StrictMode>,
);
```

- [ ] **Step 4: Run the test + full suite**

Run: `pnpm test` (all widgets/features/app green); `pnpm typecheck`; `pnpm build`. All pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/app apps/web/src/pages apps/web/src/main.tsx
git commit -m "feat(web): wire app shell, router, and pages"
```

---

### Task 12: Playwright e2e + FSD boundary lint + finalize

**Files:**
- Create: `apps/web/playwright.config.ts`, `apps/web/tests/e2e/review.spec.ts`, `apps/web/src/shared/test/browser.ts`, `apps/web/public/mockServiceWorker.js` (via `pnpm dlx msw init public`), `apps/web/steiger.config.ts`, `apps/web/README.md`; edit `apps/web/src/main.tsx` (conditional worker start), `.github/workflows/ci.yml` (add steiger + playwright steps).

**Interfaces:**
- Produces: an e2e happy path (pick deck → review a card) served by the Vite dev server with the MSW **browser** worker returning canned data (so e2e needs no backend); Steiger enforcing FSD layer boundaries; a web README.

- [ ] **Step 1: Set up the MSW browser worker (dev/e2e only)**

Run: `cd apps/web && pnpm dlx msw init public --save`
`apps/web/src/shared/test/browser.ts`:
```ts
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);
```
Edit `apps/web/src/main.tsx` to start the worker only when `VITE_ENABLE_MSW` is set:
```tsx
async function enableMocking() {
  if (import.meta.env.VITE_ENABLE_MSW !== "true") return;
  const { worker } = await import("./shared/test/browser");
  await worker.start({ onUnhandledRequest: "bypass" });
}
enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(
    <StrictMode><App /></StrictMode>,
  );
});
```
(Keep the existing `import { App }` / css imports; wrap the render as above.)

- [ ] **Step 2: Write the Playwright config + failing e2e spec**

`apps/web/playwright.config.ts`:
```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  use: { baseURL: "http://localhost:5173" },
  webServer: {
    command: "VITE_ENABLE_MSW=true pnpm dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
```
`apps/web/tests/e2e/review.spec.ts`:
```ts
import { expect, test } from "@playwright/test";

test("reveal and rate a card", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Vocab Trainer" })).toBeVisible();
  // default MSW handlers return an empty queue → the caught-up state renders
  await expect(page.getByText(/caught up|pick a deck/i)).toBeVisible();
});
```
Install browsers: `pnpm dlx playwright install --with-deps chromium`.

- [ ] **Step 3: Run the e2e to verify it passes**

Run: `pnpm exec playwright test`
Expected: 1 passed. (If it fails because the app needs a deck selected first, adjust the assertion to the actual default screen — the app with no deck shows "Pick a deck to start.")

- [ ] **Step 4: Add Steiger FSD boundary lint**

`apps/web/steiger.config.ts`:
```ts
import { defineConfig } from "steiger";
import fsd from "@feature-sliced/steiger-plugin";

export default defineConfig([...fsd.configs.recommended]);
```
Run: `pnpm exec steiger ./src` and fix any real boundary violations it reports (there should be none if imports followed the plan). Add `"fsd": "steiger ./src"` to package.json scripts.

- [ ] **Step 5: Prove the boundary rule bites (temporary negative check)**

Add an illegal upward import to a low layer — e.g. in `src/shared/lib/utils.ts` add `import { ReviewSession } from "@/widgets/review-session";` — run `pnpm exec steiger ./src`, confirm it reports a violation, then **revert** the line and confirm a clean run.

- [ ] **Step 6: Finalize CI + README**

Edit `.github/workflows/ci.yml` `web` job — add after `pnpm test`:
```yaml
      - run: pnpm fsd
      - run: pnpm dlx playwright install --with-deps chromium
      - run: pnpm exec playwright test
```
`apps/web/README.md`:
```markdown
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
pnpm lint && pnpm typecheck && pnpm test && pnpm fsd && pnpm build
```

## Layers (FSD)

`app → pages → widgets → features → entities → shared` — imports flow downward only.
```

- [ ] **Step 7: Full green run and commit**

Run:
```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm fsd && pnpm build && pnpm exec playwright test
```
Expected: all pass.
```bash
git add apps/web .github/workflows/ci.yml
git commit -m "test(web): add e2e happy path and enforce FSD boundaries"
```

---

## Definition of Done (Plan 2)

- `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm fsd`, `pnpm build`, and `pnpm exec playwright test` all pass.
- `pnpm dev` serves an app that (with the backend running) lets you pick/create a deck, import words with a dry-run preview then commit, run a review session (reveal → rate with mouse or `1`–`4` keys → advance), and view stats.
- FSD boundaries enforced by Steiger; the typed client is generated from the backend's OpenAPI schema.
- **Next:** Plan 3 adds the LLM providers + sentence-practice endpoints and the practice/pronunciation UI (a new `features/check-sentence`, `features/pronounce`, and a Practice page).
