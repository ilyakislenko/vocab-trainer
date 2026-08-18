import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  startRecognition: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => true),
}));

import { recognizeOnce, speak } from "@/shared/lib/speech";
import { PronounceControls } from "./PronounceControls";

function stubRecorder() {
  class FakeRecorder {
    mimeType = "audio/webm";
    state: "inactive" | "recording" = "inactive";
    ondataavailable: ((e: { data: Blob }) => void) | null = null;
    onstop: (() => void) | null = null;
    onerror: (() => void) | null = null;

    start() {
      this.state = "recording";
      queueMicrotask(() => {
        this.ondataavailable?.({ data: new Blob(["fake-audio"], { type: "audio/webm" }) });
        this.onstop?.();
      });
    }

    stop() {
      this.state = "inactive";
    }
  }
  vi.stubGlobal("MediaRecorder", FakeRecorder);
  Object.defineProperty(navigator, "mediaDevices", {
    value: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [] }) },
    configurable: true,
  });
}

describe("PronounceControls", () => {
  it("speaks the word", async () => {
    renderWithProviders(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /hear it|слушать/i }));
    expect(speak).toHaveBeenCalledWith("run");
  });

  it("shows a match when the transcript equals the word", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("run");
    renderWithProviders(<PronounceControls word="Run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it|говорить/i }));
    await waitFor(() => expect(screen.getByText(/✓/)).toBeInTheDocument());
  });

  it("shows what was heard on a mismatch", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("ran");
    renderWithProviders(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it|говорить/i }));
    await waitFor(() => expect(screen.getByText(/ran/)).toBeInTheDocument());
  });

  it("matches when the target word appears inside a spoken sentence", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("i need to run to the store before it closes");
    renderWithProviders(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it|говорить/i }));
    await waitFor(() => expect(screen.getByText(/✓/)).toBeInTheDocument());
    expect(screen.queryByText(/try again/i)).not.toBeInTheDocument();
  });

  it("checks grammar and shows native alternatives when the sentence needs work", async () => {
    server.use(
      http.post("/api/practice/check", () =>
        HttpResponse.json({
          verdict: "needs_work",
          feedback: "Past tense of 'run' is 'ran'.",
          corrected: "I ran to the store yesterday.",
          example: "She runs every morning.",
        }),
      ),
    );
    vi.mocked(recognizeOnce).mockResolvedValueOnce("i run to the store yesterday");
    renderWithProviders(<PronounceControls word="run" cardId={1} />);
    await userEvent.click(screen.getByRole("button", { name: /say it|говорить/i }));
    await waitFor(() => expect(screen.getByText(/say it like|говори как/i)).toBeInTheDocument());
    expect(screen.getByText(/I ran to the store yesterday\./)).toBeInTheDocument();
    expect(screen.getByText(/native way|по-настоящему/i)).toBeInTheDocument();
  });

  it("confirms the match when the spoken sentence is grammatically fine", async () => {
    server.use(
      http.post("/api/practice/check", () =>
        HttpResponse.json({
          verdict: "ok",
          feedback: "Looks good.",
          corrected: null,
          example: "I run daily.",
        }),
      ),
    );
    vi.mocked(recognizeOnce).mockResolvedValueOnce("i need to run to the store");
    renderWithProviders(<PronounceControls word="run" cardId={1} />);
    await userEvent.click(screen.getByRole("button", { name: /say it|говорить/i }));
    await waitFor(() => expect(screen.getByText(/✓ nice|✓ отлично/i)).toBeInTheDocument());
  });

  it("shows the example sentence and matches a spoken version", async () => {
    server.use(
      http.get("/api/practice/example", () =>
        HttpResponse.json({ example: "She runs every morning." }),
      ),
    );
    vi.mocked(recognizeOnce).mockResolvedValueOnce("she runs every morning");
    renderWithProviders(<PronounceControls word="run" cardId={1} />);
    await waitFor(() => expect(screen.getByText(/She runs every morning/)).toBeInTheDocument());
    await userEvent.click(
      screen.getByRole("button", { name: /say the sentence|произнеси предложение/i }),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/great job on the sentence|отлично, предложение/i),
      ).toBeInTheDocument(),
    );
  });

  it("reports missing words when the spoken sentence differs", async () => {
    server.use(
      http.get("/api/practice/example", () =>
        HttpResponse.json({ example: "She runs every morning." }),
      ),
    );
    vi.mocked(recognizeOnce).mockResolvedValueOnce("she runs");
    renderWithProviders(<PronounceControls word="run" cardId={1} />);
    await waitFor(() => expect(screen.getByText(/She runs every morning/)).toBeInTheDocument());
    await userEvent.click(
      screen.getByRole("button", { name: /say the sentence|произнеси предложение/i }),
    );
    await waitFor(() =>
      expect(screen.getByText(/missing words|пропущенные слова/i)).toBeInTheDocument(),
    );
  });

  it("renders the phoneme assessment after server scoring", async () => {
    stubRecorder();
    server.use(
      http.post("/api/pronounce/score", () =>
        HttpResponse.json({
          overall: 0.92,
          words: [
            {
              word: "hello",
              score: 0.92,
              phonemes: [
                { phoneme: "h", score: 0.95, verdict: "good" },
                { phoneme: "l", score: 0.4, verdict: "weak" },
              ],
            },
          ],
          transcript: "hello",
          scored_phonemes: true,
        }),
      ),
    );
    renderWithProviders(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /record & score|запись и оценка/i }));
    await waitFor(() => expect(screen.getByText("97%")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "hello" }));
    await waitFor(() => expect(screen.getByText(/слабо — 40%|40%/)).toBeInTheDocument());
    expect(screen.getByText(/получился слабо|keep practising/i)).toBeInTheDocument();
  });

  it("shows the offline note when the backend returns word-match only", async () => {
    stubRecorder();
    server.use(
      http.post("/api/pronounce/score", () =>
        HttpResponse.json({
          overall: 0,
          words: [],
          transcript: "",
          scored_phonemes: false,
        }),
      ),
    );
    renderWithProviders(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /record & score|запись и оценка/i }));
    await waitFor(() =>
      expect(
        screen.getByText(/phoneme scoring is offline|фонемная оценка сейчас недоступна/i),
      ).toBeInTheDocument(),
    );
  });
});
