import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { useScorePronunciation } from "./use-score-pronunciation";

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

function Harness() {
  const score = useScorePronunciation();
  return (
    <div>
      <button type="button" onClick={() => score.mutate("hello")}>
        record
      </button>
      {score.isPending && <p>pending</p>}
      {score.data && <p>{score.data.overall}</p>}
      {score.isError && <p>error</p>}
    </div>
  );
}

describe("useScorePronunciation", () => {
  it("posts the recording and returns the assessment", async () => {
    stubRecorder();
    let target = "";
    server.use(
      http.post("/api/pronounce/score", async ({ request }) => {
        const form = await request.formData();
        target = String(form.get("target"));
        return HttpResponse.json({
          overall: 0.92,
          words: [
            {
              word: "hello",
              score: 0.92,
              phonemes: [{ phoneme: "h", score: 0.95, verdict: "good" }],
            },
          ],
          transcript: "hello",
          scored_phonemes: true,
        });
      }),
    );
    renderWithProviders(<Harness />);
    await userEvent.click(screen.getByRole("button", { name: /record/i }));
    await waitFor(() => expect(screen.getByText("0.92")).toBeInTheDocument());
    expect(target).toBe("hello");
  });

  it("surfaces errors when the endpoint fails", async () => {
    stubRecorder();
    server.use(http.post("/api/pronounce/score", () => HttpResponse.error()));
    renderWithProviders(<Harness />);
    await userEvent.click(screen.getByRole("button", { name: /record/i }));
    await waitFor(() => expect(screen.getByText("error")).toBeInTheDocument());
  });
});
