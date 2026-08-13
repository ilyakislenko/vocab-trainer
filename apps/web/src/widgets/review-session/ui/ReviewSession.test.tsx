import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
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
        ]),
      ),
      http.post("/api/review", async ({ request }) => {
        const b = (await request.json()) as { card_id: number };
        return HttpResponse.json({
          id: b.card_id,
          word: "x",
          translation: "y",
          transcription: null,
        });
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

  it("does not skip the next due card when a post-rating refetch returns a shorter queue", async () => {
    let queueCalls = 0;
    server.use(
      http.get("/api/review/queue", () => {
        queueCalls += 1;
        if (queueCalls === 1) {
          return HttpResponse.json([
            { id: 1, word: "run", translation: "бежать", transcription: null },
            { id: 2, word: "jump", translation: "прыгать", transcription: null },
          ]);
        }
        // FSRS pushed card 1's due date into the future: the live queue shrank.
        return HttpResponse.json([
          { id: 2, word: "jump", translation: "прыгать", transcription: null },
        ]);
      }),
      http.post("/api/review", async ({ request }) => {
        const b = (await request.json()) as { card_id: number };
        return HttpResponse.json({
          id: b.card_id,
          word: "x",
          translation: "y",
          transcription: null,
        });
      }),
    );

    renderWithProviders(<ReviewSession deckId={1} />);
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /show answer/i }));
    await userEvent.click(screen.getByRole("button", { name: /good/i }));

    // Let the invalidated background refetch (shrunk queue) land before asserting.
    await waitFor(() => expect(queueCalls).toBeGreaterThanOrEqual(2));

    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    expect(screen.queryByText(/caught up/i)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show answer/i }));
    await userEvent.click(screen.getByRole("button", { name: /easy/i }));
    await waitFor(() => expect(screen.getByText(/caught up/i)).toBeInTheDocument());
  });
});
