import { screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { FocusList } from "./FocusList";

const LEECH = {
  id: 7,
  skill: "art.definite",
  module_id: "b1.grammar.articles",
  source_item_id: "b1.grammar.articles.q4",
  is_leech: true,
};

function mockFocus(items: unknown[]) {
  server.use(http.get("/api/session/focus", () => HttpResponse.json(items)));
}

describe("FocusList", () => {
  it("lists leech skills and links to skill reviews", async () => {
    mockFocus([LEECH]);
    renderWithProviders(
      <MemoryRouter>
        <FocusList />
      </MemoryRouter>,
    );

    expect(await screen.findByText("art.definite")).toBeInTheDocument();
    expect(screen.getByText(/Фокус — слабые места|Focus — weak spots/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Тренировать навыки|Drill skills/i })).toHaveAttribute(
      "href",
      "/learn/skills",
    );
  });

  it("renders nothing when there are no leeches", async () => {
    mockFocus([]);
    renderWithProviders(
      <MemoryRouter>
        <FocusList />
      </MemoryRouter>,
    );

    await waitFor(() =>
      expect(screen.queryByText(/Фокус — слабые места|Focus — weak spots/)).not.toBeInTheDocument(),
    );
  });
});
