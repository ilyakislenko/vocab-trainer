import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "@/shared/test";
import { ReviewPage } from "./ReviewPage";

describe("ReviewPage", () => {
  it("resets the review session (not stuck on the old deck's cards) when the selected deck changes", async () => {
    server.use(
      http.get("/api/review/queue", ({ request }) => {
        const deckId = new URL(request.url).searchParams.get("deck_id");
        if (deckId === "2") {
          return HttpResponse.json([
            { id: 2, word: "jump", translation: "прыгать", transcription: null },
          ]);
        }
        return HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null },
        ]);
      }),
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { rerender } = render(
      <QueryClientProvider client={client}>
        <ReviewPage deckId={1} />
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());

    // Simulate switching decks via the header DeckPicker: same route, new deckId prop.
    rerender(
      <QueryClientProvider client={client}>
        <ReviewPage deckId={2} />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    expect(screen.queryByText("run")).not.toBeInTheDocument();
  });
});
