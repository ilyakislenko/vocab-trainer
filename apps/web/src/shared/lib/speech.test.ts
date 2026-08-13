import { afterEach, describe, expect, it, vi } from "vitest";
import { isSpeechSynthesisSupported, speak } from "./speech";

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
