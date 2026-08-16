import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "@/shared/test";
import { DeckSelect } from "./DeckSelect";

describe("DeckSelect", () => {
  it("shows the selected deck's name, not its id", () => {
    renderWithProviders(
      <DeckSelect decks={[{ id: 1, name: "Travel" }]} value={1} onChange={vi.fn()} />,
    );
    // The trigger must display the deck name, never the raw id "1".
    expect(screen.getByText("Travel")).toBeInTheDocument();
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });

  it("shows the placeholder when nothing is selected", () => {
    renderWithProviders(
      <DeckSelect decks={[{ id: 1, name: "Travel" }]} value={null} onChange={vi.fn()} />,
    );
    expect(screen.getByText(/select a deck|выберите колоду/i)).toBeInTheDocument();
  });
});
