import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { CurriculumMap } from "./CurriculumMap";

const MAP = {
  levels: [
    {
      level: "A1",
      modules: [
        {
          id: "a1.grammar.be",
          title: "To be",
          level: "A1",
          track: "grammar",
          availability: "authoring",
          status: "not_started",
          quiz_best_score: null,
        },
      ],
    },
    {
      level: "B1",
      modules: [
        {
          id: "b1.grammar.dependent-prepositions",
          title: "Dependent prepositions",
          level: "B1",
          track: "grammar",
          availability: "available",
          status: "in_progress",
          quiz_best_score: 80,
        },
        {
          id: "b1.grammar.perfect-aspect",
          title: "Perfect aspect",
          level: "B1",
          track: "grammar",
          availability: "available",
          status: "completed",
          quiz_best_score: 100,
        },
      ],
    },
  ],
  recommended_module_id: "b1.grammar.dependent-prepositions",
};

describe("CurriculumMap", () => {
  it("groups modules by level and links available modules to their lesson", async () => {
    server.use(http.get("/api/curriculum", () => HttpResponse.json(MAP)));
    renderWithProviders(
      <MemoryRouter>
        <CurriculumMap />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("Dependent prepositions")).toBeInTheDocument());

    expect(screen.getByText("Perfect aspect")).toBeInTheDocument();
    expect(screen.getByText(/completed|завершено/i)).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /dependent prepositions/i });
    expect(link).toHaveAttribute("href", "/learn/b1.grammar.dependent-prepositions");
  });

  it("shows authoring modules without a lesson link", async () => {
    server.use(http.get("/api/curriculum", () => HttpResponse.json(MAP)));
    renderWithProviders(
      <MemoryRouter>
        <CurriculumMap />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("To be")).toBeInTheDocument());
    expect(screen.getByText(/authoring in progress|в разработке/i)).toBeInTheDocument();
  });
});
