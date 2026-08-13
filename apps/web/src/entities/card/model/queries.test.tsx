import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
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
        HttpResponse.json([{ id: 7, word: "run", translation: "бежать", transcription: "rʌn" }]),
      ),
    );
    const { result } = renderHook(() => useReviewQueue(1), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].word).toBe("run");
  });
});
