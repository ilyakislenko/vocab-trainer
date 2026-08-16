import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ImportForm } from "./ImportForm";

describe("ImportForm", () => {
  it("previews without committing then imports", async () => {
    server.use(
      http.post("/api/decks/:id/import", async ({ request }) => {
        const body = (await request.json()) as { dry_run: boolean };
        return HttpResponse.json({
          committed: !body.dry_run,
          imported: [
            {
              id: body.dry_run ? null : 1,
              word: "run",
              translation: "бежать",
              transcription: null,
            },
          ],
          errors: [],
        });
      }),
    );
    renderWithProviders(<ImportForm deckId={1} />);
    await userEvent.type(screen.getByRole("textbox"), "run,бежать");
    await userEvent.click(screen.getByRole("button", { name: /preview|предпросмотр/i }));
    await waitFor(() => expect(screen.getByText(/1 word|1 слов/i)).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /import|импортировать/i }));
    await waitFor(() =>
      expect(screen.getByText(/imported 1|импортировано: 1/i)).toBeInTheDocument(),
    );
  });

  it("shows an inline error when the import request fails", async () => {
    server.use(
      http.post("/api/decks/:id/import", () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );
    renderWithProviders(<ImportForm deckId={1} />);
    await userEvent.type(screen.getByRole("textbox"), "run,бежать");
    await userEvent.click(screen.getByRole("button", { name: /import|импортировать/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
