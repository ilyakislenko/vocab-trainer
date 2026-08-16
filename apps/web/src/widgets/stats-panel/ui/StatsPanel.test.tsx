import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { StatsPanel } from "./StatsPanel";

describe("StatsPanel", () => {
  it("shows due and reviewed counts", async () => {
    server.use(
      http.get("/api/stats", () =>
        HttpResponse.json({
          due_today: 5,
          total_reviews: 12,
          streak: 3,
          fsrs_new: 10,
          fsrs_learning: 8,
          fsrs_review: 20,
          fsrs_relearning: 2,
          activity: [],
        }),
      ),
    );
    renderWithProviders(<StatsPanel deckId={1} />);
    await waitFor(() => expect(screen.getByText("📅")).toBeInTheDocument());
    expect(screen.getByText("📊")).toBeInTheDocument();
  });
});
