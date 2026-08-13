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
});
