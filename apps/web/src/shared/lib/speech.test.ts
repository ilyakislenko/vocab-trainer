import { afterEach, describe, expect, it, vi } from "vitest";
import {
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
  recognizeOnce,
  speak,
  startRecognition,
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
  resultIndex: number;
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal?: boolean }>;
};

class FakeRecognition {
  lang = "";
  continuous = false;
  interimResults = false;
  onresult: ((event: RecognitionResultEvent) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  start(): void {
    // Interim result first, then the final one — the browser may send several.
    this.onresult?.({
      resultIndex: 0,
      results: [{ 0: { transcript: "  Christian  " }, isFinal: false, length: 1 }],
    });
    this.onresult?.({
      resultIndex: 0,
      results: [{ 0: { transcript: "  Hoisting  " }, isFinal: true, length: 1 }],
    });
  }
  stop(): void {
    this.onend?.();
  }
}

class ContinuousRecognition {
  lang = "";
  continuous = true;
  interimResults = true;
  onresult: ((event: RecognitionResultEvent) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  start(): void {
    // Several final results arrive as the user speaks in bursts; each event
    // carries the full accumulated results list like the browser API does.
    this.onresult?.({
      resultIndex: 0,
      results: [
        { 0: { transcript: "  first  " }, isFinal: true, length: 1 },
        { 0: { transcript: "second" }, isFinal: true, length: 1 },
      ],
    });
  }
  stop(): void {
    this.onend?.();
  }
}

class InterimOnlyRecognition {
  lang = "";
  continuous = false;
  interimResults = false;
  onresult: ((event: RecognitionResultEvent) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  start(): void {
    this.onresult?.({
      resultIndex: 0,
      results: [{ 0: { transcript: "ability" }, isFinal: false, length: 1 }],
    });
    this.onend?.();
  }
  stop(): void {
    this.onend?.();
  }
}

class FailingRecognition {
  lang = "";
  continuous = false;
  interimResults = false;
  onresult: ((event: RecognitionResultEvent) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  start(): void {
    this.onerror?.(new Error("boom"));
  }
  stop(): void {
    this.onend?.();
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

  it("waits for the final transcript instead of an interim one", async () => {
    vi.stubGlobal("SpeechRecognition", FakeRecognition);
    await expect(recognizeOnce()).resolves.toBe("hoisting");
  });

  it("rejects when recognition ends without a final result", async () => {
    vi.stubGlobal("SpeechRecognition", InterimOnlyRecognition);
    await expect(recognizeOnce()).rejects.toThrow(/without a final result/);
  });

  it("rejects when recognition emits an error", async () => {
    vi.stubGlobal("SpeechRecognition", FailingRecognition);
    await expect(recognizeOnce()).rejects.toThrow();
  });
});

describe("startRecognition", () => {
  it("returns null when speech recognition is unsupported", () => {
    vi.stubGlobal("SpeechRecognition", undefined);
    vi.stubGlobal("webkitSpeechRecognition", undefined);
    expect(startRecognition()).toBeNull();
  });

  it("stays open across pauses and resolves with the joined transcript on stop", async () => {
    vi.stubGlobal("SpeechRecognition", ContinuousRecognition);
    const session = startRecognition();
    if (session === null) throw new Error("expected a session");
    const promise = session.result;
    session.stop();
    await expect(promise).resolves.toBe("first second");
  });

  it("rejects when recognition ends on its own without a stop", async () => {
    vi.stubGlobal("SpeechRecognition", InterimOnlyRecognition);
    const session = startRecognition();
    if (session === null) throw new Error("expected a session");
    await expect(session.result).rejects.toThrow(/without a result/);
  });

  it("rejects when recognition emits an error", async () => {
    vi.stubGlobal("SpeechRecognition", FailingRecognition);
    const session = startRecognition();
    if (session === null) throw new Error("expected a session");
    await expect(session.result).rejects.toThrow();
  });
});
