import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PhrasePractice } from "./PhrasePractice";

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

const MULTI_WORD_ASSESSMENT = {
  overall: 0.9,
  words: [
    {
      word: "i",
      score: 0.9,
      phonemes: [{ phoneme: "aɪ", score: 0.9, verdict: "good" }],
    },
    {
      word: "optimize",
      score: 0.4,
      phonemes: [{ phoneme: "z", score: 0.4, verdict: "weak" }],
    },
  ],
  transcript: "i optimize",
  scored_phonemes: true,
};

describe("PhrasePractice", () => {
  it("lists phrases for the selected category", () => {
    renderWithProviders(<PhrasePractice />);
    expect(screen.getByText(/optimize re-renders with memoization/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /I optimize re-renders with memoization/i }),
    ).toBeInTheDocument();
  });

  it("shows the record control with the phrase as the target after selection", async () => {
    renderWithProviders(<PhrasePractice />);
    await userEvent.click(
      screen.getByRole("button", { name: /I optimize re-renders with memoization/i }),
    );
    expect(
      screen.getByRole("button", { name: /record & score|запись и оценка/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /hear|прослушать/i })).toBeInTheDocument();
  });

  it("renders the per-phoneme assessment from a mocked /pronounce/score", async () => {
    stubRecorder();
    server.use(http.post("/api/pronounce/score", () => HttpResponse.json(MULTI_WORD_ASSESSMENT)));
    renderWithProviders(<PhrasePractice />);
    await userEvent.click(
      screen.getByRole("button", { name: /I optimize re-renders with memoization/i }),
    );
    await userEvent.click(screen.getByRole("button", { name: /record & score|запись и оценка/i }));
    await waitFor(() => expect(screen.getByText("96%")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "optimize" })).toBeInTheDocument();
  });
});
