import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
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

function renderSession(cards: unknown[] = CARDS) {
  return renderWithProviders(
    <MemoryRouter>
      <PracticeSession cards={cards as never} isLoading={false} />
    </MemoryRouter>,
  );
}

describe("PracticeSession", () => {
  it("practises the first word and advances", async () => {
    renderSession();
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
  });

  it("shows a caught-up message when there is nothing to practise", async () => {
    renderSession([]);
    await waitFor(() => expect(screen.getByText(/нечего|nothing/i)).toBeInTheDocument());
  });

  it("navigates back to the previous word", async () => {
    renderSession();
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
    await userEvent.click(screen.getByRole("button", { name: /назад|back/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
  });

  it("shows progress bar and card face with translation", async () => {
    renderSession();
    await waitFor(() => {
      expect(screen.getByText("1 / 2")).toBeInTheDocument();
      expect(screen.getByText("бежать")).toBeInTheDocument();
      expect(screen.getByText(/rʌn/)).toBeInTheDocument();
      expect(screen.getByText("main")).toBeInTheDocument();
    });
  });

  it("back button is disabled at the first word", async () => {
    renderSession();
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
    renderSession();
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /example|пример/i }));
    await waitFor(() => expect(screen.getByText(/Unique example sentence/)).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
    expect(screen.queryByText(/Unique example sentence/)).not.toBeInTheDocument();
  });

  it("finishes the run with a completion screen and can restart", async () => {
    renderSession();
    const main = document.body;
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
    await userEvent.click(screen.getByRole("button", { name: /далее|continue/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("jump"));
    await userEvent.click(screen.getByRole("button", { name: /завершить|finish/i }));
    await waitFor(() =>
      expect(screen.getByText(/Тренировка завершена|Run complete/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/2\s+слов пройдено|2\s+words practised/)).toBeInTheDocument();
    const backLinks = screen.getAllByRole("link", { name: /назад к плану|back to curriculum/i });
    expect(backLinks.length).toBeGreaterThanOrEqual(1);
    for (const link of backLinks) expect(link).toHaveAttribute("href", "/learn");
    await userEvent.click(screen.getByRole("button", { name: /повторить ещё|practise more/i }));
    await waitFor(() => expect(main.querySelector(".text-4xl")).toHaveTextContent("run"));
  });
});
