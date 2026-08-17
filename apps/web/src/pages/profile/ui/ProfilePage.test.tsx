import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ProfilePage } from "./ProfilePage";

function mockProfile() {
  server.use(
    http.get("/api/decks", () => HttpResponse.json([{ id: 1, name: "Travel" }])),
    http.get("/api/stats", () =>
      HttpResponse.json({
        due_today: 3,
        total_reviews: 120,
        streak: 4,
        fsrs_new: 40,
        fsrs_learning: 8,
        fsrs_review: 70,
        fsrs_relearning: 2,
        activity: [],
      }),
    ),
    http.get("/api/progress", () =>
      HttpResponse.json({
        levels: [
          { level: "A1", completed: 1, total: 10 },
          { level: "B1", completed: 2, total: 10 },
        ],
        overall_percent: 15,
        streak: 4,
        has_reviewed: true,
      }),
    ),
  );
}

describe("ProfilePage", () => {
  it("renders level, streak, total reviews, card states, and curriculum progress", async () => {
    server.use(
      http.get("/api/curriculum", () =>
        HttpResponse.json({ levels: [], recommended_module_id: null, placement_level: "B1" }),
      ),
    );
    mockProfile();
    renderWithProviders(
      <MemoryRouter>
        <ProfilePage deckId={1} />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getAllByText(/B1/).length).toBeGreaterThan(0));
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText(/40/)).toBeInTheDocument();
    expect(screen.getByText(/15%/)).toBeInTheDocument();
    expect(screen.getByText(/A1/)).toBeInTheDocument();
    expect(screen.queryByText(/take the level test|пройти тест/i)).not.toBeInTheDocument();
  });

  it("shows the level-test CTA when not assessed", async () => {
    server.use(
      http.get("/api/curriculum", () =>
        HttpResponse.json({ levels: [], recommended_module_id: null, placement_level: null }),
      ),
    );
    mockProfile();
    renderWithProviders(
      <MemoryRouter>
        <ProfilePage deckId={1} />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText(/not assessed|не определён/i)).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /take the level test|пройти тест/i })).toHaveAttribute(
      "href",
      "/placement",
    );
  });
});
