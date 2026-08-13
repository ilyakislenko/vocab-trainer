# Vocab Trainer — Plan 4: Frontend Practice + Pronunciation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the last user-facing loop to the React frontend: practise building a sentence with a card's word and get LLM feedback, request an example, and use pronunciation (hear the word via TTS, record yourself and self-check via speech-to-text). Wire it into a new Practice page.

**Architecture:** Same Feature-Sliced Design frontend (`apps/web`). Regenerate the typed `openapi-fetch` client so the backend's `/practice/*` endpoints are available. New `features/check-sentence` (LLM feedback + example) and `features/pronounce` (Web Speech, behind feature-detected `shared/lib` helpers), a `widgets/practice-session`, and a `pages/practice` wired into the app nav.

**Tech Stack:** existing (React 19, TS strict, Vite, TanStack Query, shadcn/ui, MSW, Vitest, Steiger) + the browser **Web Speech API** (`speechSynthesis`, `SpeechRecognition`) wrapped in `shared/lib/speech.ts`.

## Global Constraints

- Web work under `apps/web/`; run commands from there. **pnpm**.
- **FSD is law** (Steiger-enforced): imports downward only `app → pages → widgets → features → entities → shared`; slices via public `index.ts`; no cross-slice/sideways imports.
- Types: `pnpm typecheck` strict clean; no `any`, no non-null `!` to dodge the checker.
- Quality: no placeholders/dead code. Business/data logic in `features`/`entities` model, not shared UI.
- **API contract (from the Plan-3 backend — regenerate, don't invent):**
  - `POST /practice/check` `{card_id, sentence}` → `FeedbackOut {verdict:"ok"|"needs_work", feedback, corrected:string|null, example:string|null}`
  - `GET /practice/example?card_id=` → `ExampleOut {example}`
  - MSW handlers mock `"/api/practice/..."`. A provider-down backend returns **502**.
- **Web Speech is browser-only** (absent in jsdom): all access goes through `shared/lib/speech.ts`, which feature-detects and no-ops/reports unsupported. Component tests mock that module — they never touch real `speechSynthesis`/`SpeechRecognition`.
- Commits: Conventional Commits; **no assistant/tool attribution**.

## File Structure (additions)

```
apps/web/
  openapi.json                              # regenerated (edit)
  src/shared/api/schema.d.ts                # regenerated (edit)
  src/shared/api/types.ts                   # + Feedback (edit)
  src/shared/lib/speech.ts                  # Web Speech wrappers (feature-detected)
  src/features/check-sentence/model/use-practice.ts
  src/features/check-sentence/ui/SentencePractice.tsx
  src/features/check-sentence/index.ts
  src/features/pronounce/ui/PronounceControls.tsx
  src/features/pronounce/index.ts
  src/widgets/practice-session/ui/PracticeSession.tsx
  src/widgets/practice-session/index.ts
  src/pages/practice/ui/PracticePage.tsx
  src/pages/practice/index.ts
  src/app/App.tsx                           # + Practice nav + route (edit)
  src/shared/test/handlers.ts               # + practice handlers (edit)
  tests/e2e/practice.spec.ts
```

---

### Task 1: Regenerate the typed API client for `/practice/*`

**Files:**
- Modify: `apps/web/openapi.json` (re-export), `apps/web/src/shared/api/schema.d.ts` (regenerate), `apps/web/src/shared/api/types.ts` (add `Feedback`), `apps/web/src/shared/test/handlers.ts` (add default practice handlers)
- Create: `apps/web/src/shared/api/practice.test.ts`

**Interfaces:**
- Produces: `Feedback = components["schemas"]["FeedbackOut"]` exported from `shared/api`; the generated `paths` include `/practice/check` (POST) and `/practice/example` (GET). Default MSW handlers for both.

- [ ] **Step 1: Regenerate the schema from the backend**

Run from repo root:
```bash
cd apps/api
uv run python -c "import json; from vocab_api.main import create_app; print(json.dumps(create_app().openapi(), indent=2))" > ../web/openapi.json
cd ../web
pnpm gen:api          # regenerates src/shared/api/schema.d.ts
pnpm exec biome format --write openapi.json src/shared/api/schema.d.ts
```
Verify the new `paths` keys exist in `schema.d.ts`: `"/practice/check"` and `"/practice/example"`, and `components["schemas"]` now has `FeedbackOut`, `CheckSentenceIn`, `ExampleOut`.

- [ ] **Step 2: Add the `Feedback` type + a failing test**

Add to `apps/web/src/shared/api/types.ts`:
```ts
export type Feedback = components["schemas"]["FeedbackOut"];
```
Add the export to `apps/web/src/shared/api/index.ts` (`export type { ..., Feedback } from "./types";`).
Add default handlers to `apps/web/src/shared/test/handlers.ts` (inside the `handlers` array):
```ts
  http.post("/api/practice/check", () =>
    HttpResponse.json({ verdict: "ok", feedback: "Looks good.", corrected: null, example: "I run daily." })),
  http.get("/api/practice/example", () => HttpResponse.json({ example: "She runs every morning." })),
```
`apps/web/src/shared/api/practice.test.ts`:
```ts
import { describe, expect, it } from "vitest";
import { apiClient } from "@/shared/api";

describe("practice api", () => {
  it("checks a sentence via the typed client", async () => {
    const { data } = await apiClient.POST("/practice/check", {
      body: { card_id: 1, sentence: "I run daily." },
    });
    expect(data?.verdict).toBe("ok");
  });
  it("fetches an example", async () => {
    const { data } = await apiClient.GET("/practice/example", { params: { query: { card_id: 1 } } });
    expect(data?.example).toContain("runs");
  });
});
```

- [ ] **Step 3: Run tests + typecheck**

Run: `pnpm test src/shared/api/practice.test.ts` → PASS (proves the regenerated paths type-check and MSW intercepts); `pnpm typecheck` → clean; `pnpm lint` → clean.

- [ ] **Step 4: Commit**

```bash
git add apps/web/openapi.json apps/web/src/shared/api apps/web/src/shared/test/handlers.ts
git commit -m "feat(web): regenerate typed client for practice endpoints"
```

---

### Task 2: `shared/lib/speech.ts` — feature-detected Web Speech wrappers

**Files:**
- Create: `apps/web/src/shared/lib/speech.ts`, `apps/web/src/shared/lib/speech.test.ts`

**Interfaces:**
- Produces:
  - `isSpeechSynthesisSupported(): boolean`
  - `speak(text: string): void` — speaks via `speechSynthesis` if supported, else no-op.
  - `isSpeechRecognitionSupported(): boolean`
  - `recognizeOnce(): Promise<string>` — starts recognition, resolves with the first transcript (lowercased/trimmed), rejects if unsupported or on error.

- [ ] **Step 1: Write the failing test**

`apps/web/src/shared/lib/speech.test.ts`:
```ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { isSpeechSynthesisSupported, speak } from "./speech";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("speak", () => {
  it("no-ops when speechSynthesis is unsupported", () => {
    vi.stubGlobal("speechSynthesis", undefined);
    expect(isSpeechSynthesisSupported()).toBe(false);
    expect(() => speak("run")).not.toThrow();
  });

  it("calls speechSynthesis.speak with an utterance when supported", () => {
    const speakSpy = vi.fn();
    vi.stubGlobal("speechSynthesis", { speak: speakSpy, cancel: vi.fn() });
    vi.stubGlobal(
      "SpeechSynthesisUtterance",
      class {
        text: string;
        constructor(text: string) {
          this.text = text;
        }
      },
    );
    expect(isSpeechSynthesisSupported()).toBe(true);
    speak("run");
    expect(speakSpy).toHaveBeenCalledOnce();
    expect(speakSpy.mock.calls[0][0].text).toBe("run");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `pnpm test src/shared/lib/speech.test.ts` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/shared/lib/speech.ts`:
```ts
export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window && window.speechSynthesis != null;
}

export function speak(text: string): void {
  if (!isSpeechSynthesisSupported()) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

type RecognitionCtor = new () => {
  lang: string;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: unknown) => void) | null;
  start: () => void;
};

function getRecognitionCtor(): RecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: RecognitionCtor;
    webkitSpeechRecognition?: RecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function isSpeechRecognitionSupported(): boolean {
  return getRecognitionCtor() !== null;
}

export function recognizeOnce(): Promise<string> {
  const Ctor = getRecognitionCtor();
  if (Ctor === null) return Promise.reject(new Error("Speech recognition is not supported"));
  return new Promise<string>((resolve, reject) => {
    const recognition = new Ctor();
    recognition.lang = "en-US";
    recognition.onresult = (event) => {
      resolve(event.results[0][0].transcript.trim().toLowerCase());
    };
    recognition.onerror = () => reject(new Error("Speech recognition failed"));
    recognition.start();
  });
}
```

- [ ] **Step 4: Run test + typecheck**

Run: `pnpm test src/shared/lib/speech.test.ts` → PASS; `pnpm typecheck` → clean; `pnpm lint` → clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/shared/lib/speech.ts apps/web/src/shared/lib/speech.test.ts
git commit -m "feat(web): add feature-detected Web Speech helpers"
```

---

### Task 3: `features/check-sentence` — practice form + LLM feedback

**Files:**
- Create: `apps/web/src/features/check-sentence/model/use-practice.ts`, `apps/web/src/features/check-sentence/ui/SentencePractice.tsx`, `apps/web/src/features/check-sentence/index.ts`, `apps/web/src/features/check-sentence/ui/SentencePractice.test.tsx`

**Interfaces:**
- Consumes: `apiClient`, `Feedback` from `@/shared/api`; `Button`, `Textarea` from `@/shared/ui`.
- Produces:
  - `useCheckSentence(cardId)` → mutation `(sentence: string) => Feedback` (POST /practice/check).
  - `useSuggestExample(cardId)` → mutation `() => string` (GET /practice/example, returns `example`).
  - `SentencePractice({ cardId, word })` — shows the word, a textarea, a "Check" button → renders the returned feedback (verdict badge, feedback text, corrected sentence, example); a "Get an example" button → shows the suggested example; a `role="alert"` on `isError` (a 502 provider failure).

- [ ] **Step 1: Write the failing test**

`apps/web/src/features/check-sentence/ui/SentencePractice.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { SentencePractice } from "./SentencePractice";

describe("SentencePractice", () => {
  it("checks a sentence and shows feedback", async () => {
    server.use(
      http.post("/api/practice/check", () =>
        HttpResponse.json({ verdict: "needs_work", feedback: "Wrong tense.", corrected: "I ran.", example: "I run daily." })),
    );
    renderWithProviders(<SentencePractice cardId={1} word="run" />);
    await userEvent.type(screen.getByRole("textbox"), "I runned.");
    await userEvent.click(screen.getByRole("button", { name: /check/i }));
    await waitFor(() => expect(screen.getByText(/wrong tense/i)).toBeInTheDocument());
    expect(screen.getByText(/I ran\./)).toBeInTheDocument();
  });

  it("shows a provider-error alert on failure", async () => {
    server.use(
      http.post("/api/practice/check", () => HttpResponse.json({ detail: "unavailable" }, { status: 502 })),
    );
    renderWithProviders(<SentencePractice cardId={1} word="run" />);
    await userEvent.type(screen.getByRole("textbox"), "I run.");
    await userEvent.click(screen.getByRole("button", { name: /check/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `pnpm test src/features/check-sentence` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/features/check-sentence/model/use-practice.ts`:
```ts
import { useMutation } from "@tanstack/react-query";
import { apiClient, type Feedback } from "@/shared/api";

export function useCheckSentence(cardId: number) {
  return useMutation({
    mutationFn: async (sentence: string): Promise<Feedback> => {
      const { data, error } = await apiClient.POST("/practice/check", {
        body: { card_id: cardId, sentence },
      });
      if (error) throw new Error("Check failed");
      return data;
    },
  });
}

export function useSuggestExample(cardId: number) {
  return useMutation({
    mutationFn: async (): Promise<string> => {
      const { data, error } = await apiClient.GET("/practice/example", {
        params: { query: { card_id: cardId } },
      });
      if (error) throw new Error("Example failed");
      return data.example;
    },
  });
}
```
`apps/web/src/features/check-sentence/ui/SentencePractice.tsx`:
```tsx
import { useState } from "react";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { useCheckSentence, useSuggestExample } from "../model/use-practice";

export function SentencePractice({ cardId, word }: { cardId: number; word: string }) {
  const [sentence, setSentence] = useState("");
  const check = useCheckSentence(cardId);
  const example = useSuggestExample(cardId);
  const feedback = check.data;

  return (
    <div className="flex flex-col gap-3">
      <p>
        Write a sentence using <span className="font-semibold">{word}</span>:
      </p>
      <Textarea value={sentence} onChange={(e) => setSentence(e.target.value)} rows={3} />
      <div className="flex gap-2">
        <Button onClick={() => check.mutate(sentence)} disabled={check.isPending || !sentence.trim()}>
          Check
        </Button>
        <Button variant="secondary" onClick={() => example.mutate()} disabled={example.isPending}>
          Get an example
        </Button>
      </div>
      {check.isError && <p role="alert" className="text-destructive">The language model is unavailable.</p>}
      {feedback && (
        <div className="rounded-md border p-3 text-sm">
          <span className={feedback.verdict === "ok" ? "text-green-600" : "text-amber-600"}>
            {feedback.verdict === "ok" ? "Looks good" : "Needs work"}
          </span>
          <p>{feedback.feedback}</p>
          {feedback.corrected && <p>Corrected: {feedback.corrected}</p>}
          {feedback.example && <p className="text-muted-foreground">e.g. {feedback.example}</p>}
        </div>
      )}
      {example.data && <p className="text-muted-foreground text-sm">Example: {example.data}</p>}
    </div>
  );
}
```
`apps/web/src/features/check-sentence/index.ts`:
```ts
export { SentencePractice } from "./ui/SentencePractice";
export { useCheckSentence, useSuggestExample } from "./model/use-practice";
```

- [ ] **Step 4: Run the tests**

Run: `pnpm test src/features/check-sentence` → PASS; `pnpm typecheck` → clean; `pnpm lint` → clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/check-sentence
git commit -m "feat(web): add check-sentence practice feature"
```

---

### Task 4: `features/pronounce` — TTS + record-and-check

**Files:**
- Create: `apps/web/src/features/pronounce/ui/PronounceControls.tsx`, `apps/web/src/features/pronounce/index.ts`, `apps/web/src/features/pronounce/ui/PronounceControls.test.tsx`

**Interfaces:**
- Consumes: `speak`, `recognizeOnce`, `isSpeechRecognitionSupported` from `@/shared/lib/speech`; `Button` from `@/shared/ui`.
- Produces: `PronounceControls({ word })` — a 🔊 "Hear it" button (calls `speak(word)`); a 🎤 "Say it" button (calls `recognizeOnce()`, compares the transcript to `word.toLowerCase()`, shows ✓ match / ✗ with what was heard). The 🎤 button is disabled with a note when recognition is unsupported.

- [ ] **Step 1: Write the failing test**

`apps/web/src/features/pronounce/ui/PronounceControls.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => true),
}));

import { recognizeOnce, speak } from "@/shared/lib/speech";
import { PronounceControls } from "./PronounceControls";

describe("PronounceControls", () => {
  it("speaks the word", async () => {
    render(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /hear it/i }));
    expect(speak).toHaveBeenCalledWith("run");
  });

  it("shows a match when the transcript equals the word", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("run");
    render(<PronounceControls word="Run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it/i }));
    await waitFor(() => expect(screen.getByText(/✓/)).toBeInTheDocument());
  });

  it("shows what was heard on a mismatch", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("ran");
    render(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it/i }));
    await waitFor(() => expect(screen.getByText(/ran/)).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `pnpm test src/features/pronounce` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/features/pronounce/ui/PronounceControls.tsx`:
```tsx
import { useState } from "react";
import { isSpeechRecognitionSupported, recognizeOnce, speak } from "@/shared/lib/speech";
import { Button } from "@/shared/ui/button";

type Result = { heard: string; match: boolean };

export function PronounceControls({ word }: { word: string }) {
  const [result, setResult] = useState<Result | null>(null);
  const [listening, setListening] = useState(false);
  const recognitionSupported = isSpeechRecognitionSupported();

  const record = async () => {
    setListening(true);
    setResult(null);
    try {
      const heard = await recognizeOnce();
      setResult({ heard, match: heard === word.trim().toLowerCase() });
    } catch {
      setResult({ heard: "", match: false });
    } finally {
      setListening(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => speak(word)}>🔊 Hear it</Button>
        <Button variant="outline" onClick={record} disabled={!recognitionSupported || listening}>
          🎤 Say it
        </Button>
      </div>
      {!recognitionSupported && (
        <p className="text-muted-foreground text-xs">Speech recognition isn't available in this browser.</p>
      )}
      {result && (
        <p className="text-sm">
          {result.match ? "✓ Nice — that matched!" : `✗ Heard "${result.heard || "nothing"}", try again.`}
        </p>
      )}
    </div>
  );
}
```
`apps/web/src/features/pronounce/index.ts`:
```ts
export { PronounceControls } from "./ui/PronounceControls";
```

- [ ] **Step 4: Run the tests**

Run: `pnpm test src/features/pronounce` → PASS; `pnpm typecheck` → clean; `pnpm lint` → clean.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/pronounce
git commit -m "feat(web): add pronunciation controls feature"
```

---

### Task 5: `widgets/practice-session` + `pages/practice` + nav

**Files:**
- Create: `apps/web/src/widgets/practice-session/ui/PracticeSession.tsx`, `apps/web/src/widgets/practice-session/index.ts`, `apps/web/src/pages/practice/ui/PracticePage.tsx`, `apps/web/src/pages/practice/index.ts`, `apps/web/src/widgets/practice-session/ui/PracticeSession.test.tsx`
- Modify: `apps/web/src/app/App.tsx` (add a "Practice" nav link + `/practice` route)

**Interfaces:**
- Consumes: `useReviewQueue` from `@/entities/card`; `SentencePractice` from `@/features/check-sentence`; `PronounceControls` from `@/features/pronounce`; `Button` from `@/shared/ui`.
- Produces:
  - `PracticeSession({ deckId })` — snapshots the review queue (same pattern as `ReviewSession`: capture cards once so a background refetch can't disrupt the session), shows the current card's word with `SentencePractice` + `PronounceControls`, and a "Next word" button that advances an index; shows a caught-up message when exhausted, a "pick a deck" hint handled by the page, and a loading state.
  - `PracticePage({ deckId })` — renders `PracticeSession` with `key={deckId}` (remount on deck switch) or a "pick a deck" hint when `deckId` is null.
  - App nav gains a `/practice` link + route.

- [ ] **Step 1: Write the failing test**

`apps/web/src/widgets/practice-session/ui/PracticeSession.test.tsx`:
```tsx
import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PracticeSession } from "./PracticeSession";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => false),
}));

describe("PracticeSession", () => {
  it("practises the first due word and advances", async () => {
    server.use(
      http.get("/api/review/queue", () =>
        HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null },
          { id: 2, word: "jump", translation: "прыгать", transcription: null },
        ])),
    );
    renderWithProviders(<PracticeSession deckId={1} />);
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /next word/i }));
    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
  });

  it("shows a caught-up message when nothing is due", async () => {
    server.use(http.get("/api/review/queue", () => HttpResponse.json([])));
    renderWithProviders(<PracticeSession deckId={1} />);
    await waitFor(() => expect(screen.getByText(/nothing to practise/i)).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `pnpm test src/widgets/practice-session` → FAIL (module not found).

- [ ] **Step 3: Implement**

`apps/web/src/widgets/practice-session/ui/PracticeSession.tsx`:
```tsx
import { useEffect, useState } from "react";
import type { Card } from "@/shared/api";
import { useReviewQueue } from "@/entities/card";
import { SentencePractice } from "@/features/check-sentence";
import { PronounceControls } from "@/features/pronounce";
import { Button } from "@/shared/ui/button";

export function PracticeSession({ deckId }: { deckId: number }) {
  const queue = useReviewQueue(deckId);
  const [cards, setCards] = useState<Card[] | null>(null);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (cards === null && queue.data !== undefined) setCards(queue.data);
  }, [cards, queue.data]);

  if (cards === null) return <p>Loading…</p>;
  const card = cards[index];
  if (!card) return <p className="text-lg text-muted-foreground">Nothing to practise right now 🎉</p>;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">{index + 1} / {cards.length}</p>
      {card.id !== null && <SentencePractice cardId={card.id} word={card.word} />}
      <PronounceControls word={card.word} />
      <Button variant="ghost" onClick={() => setIndex((i) => i + 1)}>Next word →</Button>
    </div>
  );
}
```
`apps/web/src/widgets/practice-session/index.ts`:
```ts
export { PracticeSession } from "./ui/PracticeSession";
```
`apps/web/src/pages/practice/ui/PracticePage.tsx`:
```tsx
import { PracticeSession } from "@/widgets/practice-session";

export function PracticePage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck to practise.</p>;
  return <PracticeSession key={deckId} deckId={deckId} />;
}
```
`apps/web/src/pages/practice/index.ts`:
```ts
export { PracticePage } from "./ui/PracticePage";
```
Edit `apps/web/src/app/App.tsx`: import `PracticePage`, add `<Link to="/practice">Practice</Link>` to the nav, and add `<Route path="/practice" element={<PracticePage deckId={deckId} />} />` to `Routes`.

- [ ] **Step 4: Run tests + full suite**

Run: `pnpm test src/widgets/practice-session` → PASS; then `pnpm test`, `pnpm typecheck`, `pnpm lint`, `pnpm fsd` (Steiger clean), `pnpm build` — all green.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/widgets/practice-session apps/web/src/pages/practice apps/web/src/app/App.tsx
git commit -m "feat(web): add practice session widget, page, and nav"
```

---

### Task 6: Practice e2e + finalize

**Files:**
- Create: `apps/web/tests/e2e/practice.spec.ts`
- Modify: `apps/web/src/shared/test/handlers.ts` (ensure the practice + review-queue browser-worker handlers return usable data for the e2e — the default queue is empty; add a non-empty default or a practice-specific handler as needed)

**Interfaces:**
- Produces: a backend-free Playwright happy path that navigates to Practice and exercises "Check" against the MSW browser worker.

- [ ] **Step 1: Make the browser worker return a practisable card**

The default `/api/review/queue` handler returns `[]`, so Practice would show the caught-up state. For the e2e (which uses the MSW browser worker), give the queue a card. Edit the default handler in `apps/web/src/shared/test/handlers.ts` so `/api/review/queue` returns one card:
```ts
  http.get("/api/review/queue", () =>
    HttpResponse.json([{ id: 1, word: "run", translation: "бежать", transcription: "rʌn" }])),
```
(Update any existing unit test that asserted an empty queue from the default handler to `server.use(...)` its own empty handler, so nothing regresses. Run `pnpm test` and fix any handler-shape fallout.)

**Cross-cutting — also update Plan 2's review e2e.** The browser-worker uses this same default handler, and `tests/e2e/review.spec.ts` (from Plan 2) currently asserts the *caught-up / pick-a-deck* state, which a non-empty queue breaks. Update `review.spec.ts` to the new reality — e.g. navigate to `/`, and assert the review card word `run` is visible and the "Show answer" button appears (a more meaningful review-flow smoke). Run `pnpm exec playwright test` and confirm BOTH e2e specs pass.

- [ ] **Step 2: Write the e2e spec**

`apps/web/tests/e2e/practice.spec.ts`:
```ts
import { expect, test } from "@playwright/test";

test("practise a sentence with LLM feedback", async ({ page }) => {
  await page.goto("/practice");
  await expect(page.getByText(/write a sentence using/i)).toBeVisible();
  await page.getByRole("textbox").fill("I run every day.");
  await page.getByRole("button", { name: /check/i }).click();
  await expect(page.getByText(/looks good/i)).toBeVisible(); // default practice handler → verdict ok
});
```

- [ ] **Step 3: Run the e2e**

Run: `pnpm exec playwright test tests/e2e/practice.spec.ts`
Expected: 1 passed. (Adjust the assertion to the app's real rendered copy if needed — keep it matching reality, not brittle.)

- [ ] **Step 4: Full green gate**

Run:
```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm fsd && pnpm build && pnpm exec playwright test
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/tests/e2e/practice.spec.ts apps/web/src/shared/test/handlers.ts
git commit -m "test(web): add practice e2e happy path"
```

---

## Definition of Done (Plan 4)

- `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm fsd`, `pnpm build`, `pnpm exec playwright test` all pass.
- A **Practice** page (with the backend running + `VOCAB_LLM_PROVIDER=api` pointed at Ollama) lets you write a sentence for a word, get LLM feedback + an example, hear the word (TTS), and record + self-check pronunciation. With the LLM off (`none`) it still loads and the check returns the disabled message; a provider 502 surfaces as an inline alert.
- FSD boundaries hold (Steiger); the typed client is regenerated from the backend's OpenAPI.
- **This completes the full learning loop** across all four plans.
