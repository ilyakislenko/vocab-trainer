import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { DeckPicker } from "./DeckPicker";

describe("DeckPicker", () => {
  it("creates a deck and selects it", async () => {
    server.use(http.post("/api/decks", () => HttpResponse.json({ id: 9, name: "Travel" })));
    const onChange = vi.fn();
    renderWithProviders(<DeckPicker value={null} onChange={onChange} />);
    await userEvent.type(screen.getByPlaceholderText(/new deck/i), "Travel");
    await userEvent.click(screen.getByRole("button", { name: /create/i }));
    await waitFor(() => expect(onChange).toHaveBeenCalledWith(9));
  });
});
