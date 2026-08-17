import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PracticePage } from "./PracticePage";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  startRecognition: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => false),
}));

function renderPage(deckId: number | null, initialEntries?: string[]) {
  return renderWithProviders(
    <MemoryRouter initialEntries={initialEntries}>
      <PracticePage deckId={deckId} />
    </MemoryRouter>,
  );
}

describe("PracticePage", () => {
  it("is empty without a deck", () => {
    renderPage(null);
    expect(screen.getByText(/no deck yet|пока нет колоды/i)).toBeInTheDocument();
  });

  it("practises due words by default", async () => {
    renderPage(1);
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("run"));
  });

  it("opens the section linked via the query param", async () => {
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
    renderPage(1, ["/practice?section=main"]);
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("run"));
    expect(document.querySelector(".text-4xl")).not.toHaveTextContent("jump");
  });

  it("shows which deck and section are being studied when linked", async () => {
    server.use(
      http.get("/api/decks/:id/cards", () =>
        HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null, section: "main" },
        ]),
      ),
    );
    renderPage(1, ["/practice?section=main"]);
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("run"));
    expect(screen.getByText(/Практикуешь раздел|Studying section/i)).toBeInTheDocument();
    expect(screen.getByText(/«main»/)).toBeInTheDocument();
    expect(screen.getByText(/Sample/)).toBeInTheDocument();
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
    renderPage(1);
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
    renderPage(1);
    await userEvent.click(screen.getByRole("button", { name: /by topic|по теме/i }));
    await userEvent.type(screen.getByRole("textbox"), "travelling");
    await userEvent.click(screen.getByRole("button", { name: /find topic words|найти слова/i }));
    await waitFor(() => expect(document.querySelector(".text-4xl")).toHaveTextContent("travel"));
  });
});
