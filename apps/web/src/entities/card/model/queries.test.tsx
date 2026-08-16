import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { server } from "@/shared/test";
import { useDeckCards, useReviewQueue, useTopicWords } from "./queries";

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
        HttpResponse.json([{ id: 7, word: "run", translation: "бежать", transcription: "rʌn" }]),
      ),
    );
    const { result } = renderHook(() => useReviewQueue(1), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].word).toBe("run");
  });
});

describe("useDeckCards", () => {
  it("collects all pages until a short one is returned", async () => {
    server.use(
      http.get("/api/decks/:id/cards", ({ request }) => {
        const url = new URL(request.url);
        const offset = Number(url.searchParams.get("offset"));
        if (offset === 0) {
          return HttpResponse.json(
            Array.from({ length: 500 }, (_, i) => ({
              id: i + 1,
              word: `w${i}`,
              translation: "t",
              transcription: null,
              section: "main",
            })),
          );
        }
        return HttpResponse.json([
          { id: 501, word: "w500", translation: "t", transcription: null, section: null },
        ]);
      }),
    );
    const { result } = renderHook(() => useDeckCards(1), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(501);
  });

  it("is disabled when no deck is selected", () => {
    const { result } = renderHook(() => useDeckCards(null), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useTopicWords", () => {
  it("is disabled until a topic is submitted", () => {
    const { result } = renderHook(() => useTopicWords(1, null), { wrapper });
    expect(result.current.fetchStatus).toBe("idle");
  });

  it("loads topic cards once a topic is given", async () => {
    const { result } = renderHook(() => useTopicWords(1, "travel"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].word).toBe("run");
  });
});
