import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ReviewSession } from "./ReviewSession";

const CARD_QUEUE = [
  { id: 1, word: "run", translation: "бежать", transcription: null },
  { id: 2, word: "jump", translation: "прыгать", transcription: null },
];

function mockSummary(summary: { next_due: string | null; reviewed_today: number }) {
  server.use(http.get("/api/review/summary", () => HttpResponse.json(summary)));
}

function mockQueue(cards: unknown[]) {
  server.use(http.get("/api/review/queue", () => HttpResponse.json(cards)));
}

function mockReview() {
  server.use(
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
}

function renderSession() {
  return renderWithProviders(
    <MemoryRouter>
      <ReviewSession deckId={1} />
    </MemoryRouter>,
  );
}

describe("ReviewSession", () => {
  it("reveals, rates, advances, and finishes", async () => {
    mockQueue(CARD_QUEUE);
    mockReview();
    mockSummary({ next_due: null, reviewed_today: 0 });
    renderSession();
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    expect(screen.queryByText("бежать")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    expect(screen.getByText("бежать")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /good|хорошо/i }));
    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    await userEvent.click(screen.getByRole("button", { name: /easy|легко/i }));
    await waitFor(() =>
      expect(screen.getByText(/session complete|сессия завершена/i)).toBeInTheDocument(),
    );
  });

  it("shows a back-to-map link to leave the session", async () => {
    mockQueue(CARD_QUEUE);
    mockReview();
    mockSummary({ next_due: null, reviewed_today: 0 });
    renderSession();
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /назад к плану|back to curriculum/i })).toHaveAttribute(
      "href",
      "/learn",
    );
  });

  it("shows the empty state when nothing is due", async () => {
    mockQueue([]);
    mockSummary({ next_due: null, reviewed_today: 0 });
    renderSession();
    await waitFor(() =>
      expect(screen.getByText(/session complete|сессия завершена/i)).toBeInTheDocument(),
    );
  });

  it("re-queues the card in-session when rated Again", async () => {
    mockQueue(CARD_QUEUE);
    mockReview();
    mockSummary({ next_due: null, reviewed_today: 0 });

    renderSession();
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    await userEvent.click(screen.getByRole("button", { name: /again|заново/i }));

    // The failed card moves to the back of the session queue...
    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    expect(screen.queryByText("run")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    await userEvent.click(screen.getByRole("button", { name: /good|хорошо/i }));

    // ...and is re-shown in the same session before it finishes.
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    expect(screen.queryByText(/session complete|сессия завершена/i)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    await userEvent.click(screen.getByRole("button", { name: /good|хорошо/i }));
    await waitFor(() =>
      expect(screen.getByText(/session complete|сессия завершена/i)).toBeInTheDocument(),
    );
  });

  it("shows an honest done screen with the next-due hint and reviewed count", async () => {
    mockQueue([]);
    mockSummary({
      next_due: new Date(Date.now() + 2 * 86_400_000).toISOString(),
      reviewed_today: 7,
    });
    renderSession();
    await waitFor(() =>
      expect(screen.getByText(/session complete|сессия завершена/i)).toBeInTheDocument(),
    );
    await waitFor(() =>
      expect(screen.getByText(/returns in 2|вернётся через 2/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/7/i)).toBeInTheDocument();
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

    renderSession();
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    await userEvent.click(screen.getByRole("button", { name: /good|хорошо/i }));

    // Let the invalidated background refetch (shrunk queue) land before asserting.
    await waitFor(() => expect(queueCalls).toBeGreaterThanOrEqual(2));

    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    expect(screen.queryByText(/session complete|сессия завершена/i)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show answer|показать/i }));
    await userEvent.click(screen.getByRole("button", { name: /easy|легко/i }));
    await waitFor(() =>
      expect(screen.getByText(/session complete|сессия завершена/i)).toBeInTheDocument(),
    );
  });
});
