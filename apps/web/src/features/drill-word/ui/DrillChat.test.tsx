import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "@/shared/test";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  startRecognition: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => true),
}));

import { startRecognition } from "@/shared/lib/speech";
import { DrillChat } from "./DrillChat";

describe("DrillChat", () => {
  it("sends a typed sentence and shows the AI reply", async () => {
    renderWithProviders(<DrillChat cardId={1} word="useCallback" onClose={() => {}} />);
    await userEvent.type(
      screen.getByPlaceholderText(/write|напиши/i),
      "I memoize with useCallback",
    );
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() => expect(screen.getByText(/Good sentence!/)).toBeInTheDocument());
    expect(screen.getByText(/Now try another/)).toBeInTheDocument();
  });

  it("fills the input from voice recognition", async () => {
    vi.mocked(startRecognition).mockReturnValue({
      result: Promise.resolve("useCallback prevents re-renders"),
      stop: vi.fn(),
    });
    renderWithProviders(<DrillChat cardId={1} word="useCallback" onClose={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: /voice input|голосовой ввод/i }));
    await userEvent.click(screen.getByRole("button", { name: /stop recording|остановить/i }));
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/write|напиши/i)).toHaveValue(
        "useCallback prevents re-renders",
      ),
    );
  });
});
