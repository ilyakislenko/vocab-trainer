import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PracticePage } from "./PracticePage";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  startRecognition: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => false),
}));

describe("PracticePage", () => {
  it("is empty without a deck", () => {
    renderWithProviders(<PracticePage deckId={null} />);
    expect(screen.getByText(/create a deck above|создай колоду/i)).toBeInTheDocument();
  });

  it("practises due words by default", async () => {
    renderWithProviders(<PracticePage deckId={1} />);
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("run"));
  });

  it("filters all words by section", async () => {
    server.use(
      http.get("/api/decks/:id/cards", () =>
        HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null, section: "main" },
          {
            id: 2,
            word: "jump",
            translation: "прыгать",
            transcription: null,
            section: "elementary",
          },
        ]),
      ),
    );
    renderWithProviders(<PracticePage deckId={1} />);
    await userEvent.click(screen.getByRole("button", { name: /all words|все слова/i }));
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("run"));

    await userEvent.click(screen.getByText(/all sections|все секции/i));
    const option = await screen.findByRole("option", { name: /main/i });
    await userEvent.click(option);
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("run"));
    expect(document.querySelector(".text-4xl")).not.toHaveTextContent("jump");
  });

  it("practises topic words after submitting a prompt", async () => {
    server.use(
      http.get("/api/practice/topic", () =>
        HttpResponse.json([
          { id: 9, word: "travel", translation: "путешествие", transcription: null, section: null },
        ]),
      ),
    );
    renderWithProviders(<PracticePage deckId={1} />);
    await userEvent.click(screen.getByRole("button", { name: /by topic|по теме/i }));
    await userEvent.type(screen.getByRole("textbox"), "travelling");
    await userEvent.click(screen.getByRole("button", { name: /find topic words|найти слова/i }));
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("travel"));
  });
});
