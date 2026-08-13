import { afterEach, describe, expect, it, vi } from "vitest";
import {
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
  recognizeOnce,
  speak,
} from "./speech";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("speak", () => {
  it("no-ops when speechSynthesis is unsupported", () => {
    vi.stubGlobal("speechSynthesis", undefined);
    expect(isSpeechSynthesisSupported()).toBe(false);
    expect(() => speak("run")).not.toThrow();
  });

  it("calls speechSynthesis.speak with an utterance when supported", () => {
    const speakSpy = vi.fn();
    vi.stubGlobal("speechSynthesis", { speak: speakSpy, cancel: vi.fn() });
    vi.stubGlobal(
      "SpeechSynthesisUtterance",
      class {
        text: string;
        constructor(text: string) {
          this.text = text;
        }
      },
    );
    expect(isSpeechSynthesisSupported()).toBe(true);
    speak("run");
    expect(speakSpy).toHaveBeenCalledOnce();
    expect(speakSpy.mock.calls[0][0].text).toBe("run");
  });
});

type RecognitionResultEvent = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

class FakeRecognition {
  lang = "";
  onresult: ((event: RecognitionResultEvent) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  start(): void {
    this.onresult?.({ results: [[{ transcript: "  Run  " }]] });
  }
}

class FailingRecognition {
  lang = "";
  onresult: ((event: RecognitionResultEvent) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  start(): void {
    this.onerror?.(new Error("boom"));
  }
}

describe("isSpeechRecognitionSupported", () => {
  it("returns true when native SpeechRecognition is present", () => {
    vi.stubGlobal("SpeechRecognition", FakeRecognition);
    expect(isSpeechRecognitionSupported()).toBe(true);
  });

  it("returns true when only the webkit-prefixed constructor is present", () => {
    vi.stubGlobal("SpeechRecognition", undefined);
    vi.stubGlobal("webkitSpeechRecognition", FakeRecognition);
    expect(isSpeechRecognitionSupported()).toBe(true);
  });

  it("returns false when neither constructor is present", () => {
    vi.stubGlobal("SpeechRecognition", undefined);
    vi.stubGlobal("webkitSpeechRecognition", undefined);
    expect(isSpeechRecognitionSupported()).toBe(false);
  });
});

describe("recognizeOnce", () => {
  it("rejects when speech recognition is unsupported", async () => {
    vi.stubGlobal("SpeechRecognition", undefined);
    vi.stubGlobal("webkitSpeechRecognition", undefined);
    await expect(recognizeOnce()).rejects.toThrow();
  });

  it("resolves with the first transcript lowercased and trimmed", async () => {
    vi.stubGlobal("SpeechRecognition", FakeRecognition);
    await expect(recognizeOnce()).resolves.toBe("run");
  });

  it("rejects when recognition emits an error", async () => {
    vi.stubGlobal("SpeechRecognition", FailingRecognition);
    await expect(recognizeOnce()).rejects.toThrow();
  });
});
