import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PracticeSession } from "./PracticeSession";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => false),
}));

describe("PracticeSession", () => {
  it("practises the first due word and advances", async () => {
    server.use(
      http.get("/api/review/queue", () =>
        HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null },
          { id: 2, word: "jump", translation: "прыгать", transcription: null },
        ]),
      ),
    );
    renderWithProviders(<PracticeSession deckId={1} />);
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /next word/i }));
    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
  });

  it("shows a caught-up message when nothing is due", async () => {
    server.use(http.get("/api/review/queue", () => HttpResponse.json([])));
    renderWithProviders(<PracticeSession deckId={1} />);
    await waitFor(() => expect(screen.getByText(/nothing to practise/i)).toBeInTheDocument());
  });

  it("clears the sentence input for the next word instead of keeping stale state", async () => {
    server.use(
      http.get("/api/review/queue", () =>
        HttpResponse.json([
          { id: 1, word: "run", translation: "бежать", transcription: null },
          { id: 2, word: "jump", translation: "прыгать", transcription: null },
        ]),
      ),
    );
    renderWithProviders(<PracticeSession deckId={1} />);
    await waitFor(() => expect(screen.getByText("run")).toBeInTheDocument());
    await userEvent.type(screen.getByRole("textbox"), "I run every day.");
    expect(screen.getByRole("textbox")).toHaveValue("I run every day.");

    await userEvent.click(screen.getByRole("button", { name: /next word/i }));
    await waitFor(() => expect(screen.getByText("jump")).toBeInTheDocument());
    expect(screen.getByRole("textbox")).toHaveValue("");
  });
});
