import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ReviewPage } from "./ReviewPage";

const QUEUE = [{ id: 1, word: "run", translation: "бежать", transcription: null }];

function renderReview(deckId: number | null) {
  return renderWithProviders(
    <MemoryRouter>
      <ReviewPage deckId={deckId} />
    </MemoryRouter>,
  );
}

function mockBase(hasReviewed: boolean) {
  server.use(
    http.get("/api/review/queue", () => HttpResponse.json(QUEUE)),
    http.get("/api/review/summary", () => HttpResponse.json({ next_due: null, reviewed_today: 0 })),
    http.get("/api/progress", () =>
      HttpResponse.json({
        levels: [],
        overall_percent: 0,
        streak: 0,
        has_reviewed: hasReviewed,
      }),
    ),
  );
}

describe("ReviewPage", () => {
  it("shows the onboarding hero on first run, then the session", async () => {
    mockBase(false);
    renderReview(1);
    await waitFor(() => expect(screen.getByText(/welcome|добро пожаловать/i)).toBeInTheDocument());
    expect(screen.getByText("run")).toBeInTheDocument();
  });

  it("skips onboarding once the user has reviewed before", async () => {
    mockBase(true);
    renderReview(1);
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    expect(screen.queryByText(/welcome|добро пожаловать/i)).not.toBeInTheDocument();
  });

  it("guides to create a deck when none exists", async () => {
    server.use(
      http.get("/api/progress", () =>
        HttpResponse.json({ levels: [], overall_percent: 0, streak: 0, has_reviewed: false }),
      ),
    );
    renderReview(null);
    await waitFor(() =>
      expect(screen.getByText(/no deck yet|пока нет колоды/i)).toBeInTheDocument(),
    );
  });
});
