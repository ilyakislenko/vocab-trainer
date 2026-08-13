import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => true),
}));

import { recognizeOnce, speak } from "@/shared/lib/speech";
import { PronounceControls } from "./PronounceControls";

describe("PronounceControls", () => {
  it("speaks the word", async () => {
    render(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /hear it/i }));
    expect(speak).toHaveBeenCalledWith("run");
  });

  it("shows a match when the transcript equals the word", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("run");
    render(<PronounceControls word="Run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it/i }));
    await waitFor(() => expect(screen.getByText(/✓/)).toBeInTheDocument());
  });

  it("shows what was heard on a mismatch", async () => {
    vi.mocked(recognizeOnce).mockResolvedValueOnce("ran");
    render(<PronounceControls word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /say it/i }));
    await waitFor(() => expect(screen.getByText(/ran/)).toBeInTheDocument());
  });
});
