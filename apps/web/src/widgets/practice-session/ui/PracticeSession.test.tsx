import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PracticeSession } from "./PracticeSession";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  startRecognition: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => false),
}));

const CARDS = [
  { id: 1, word: "run", translation: "бежать", transcription: "rʌn", section: "main" },
  { id: 2, word: "jump", translation: "прыгать", transcription: null, section: null },
];

describe("PracticeSession", () => {
  it("practises the first word and advances", async () => {
    renderWithProviders(<PracticeSession cards={CARDS} isLoading={false} />);
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
  });

  it("shows a caught-up message when there is nothing to practise", async () => {
    renderWithProviders(<PracticeSession cards={[]} isLoading={false} />);
    await waitFor(() => expect(screen.getByText(/нечего|nothing/i)).toBeInTheDocument());
  });

  it("navigates back to the previous word", async () => {
    renderWithProviders(<PracticeSession cards={CARDS} isLoading={false} />);
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
    await userEvent.click(screen.getByRole("button", { name: /назад|back/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
  });

  it("shows progress bar and card face with translation", async () => {
    renderWithProviders(<PracticeSession cards={CARDS} isLoading={false} />);
    await waitFor(() => {
      expect(screen.getByText("1 / 2")).toBeInTheDocument();
      expect(screen.getByText("бежать")).toBeInTheDocument();
      expect(screen.getByText(/rʌn/)).toBeInTheDocument();
      expect(screen.getByText("main")).toBeInTheDocument();
    });
  });

  it("back button is disabled at the first word", async () => {
    renderWithProviders(<PracticeSession cards={CARDS} isLoading={false} />);
    await waitFor(() => {
      const btn = screen.getByRole("button", { name: /назад|back/i });
      expect(btn).toBeDisabled();
    });
  });

  it("clears the suggested example when advancing to the next word", async () => {
    server.use(
      http.get("/api/practice/example", () =>
        HttpResponse.json({ example: "Unique example sentence for the test." }),
      ),
    );
    renderWithProviders(<PracticeSession cards={CARDS} isLoading={false} />);
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /example|пример/i }));
    await waitFor(() => expect(screen.getByText(/Unique example sentence/)).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
    expect(screen.queryByText(/Unique example sentence/)).not.toBeInTheDocument();
  });
});
