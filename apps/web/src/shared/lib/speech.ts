export function isSpeechSynthesisSupported(): boolean {
  return (
    typeof window !== "undefined" && "speechSynthesis" in window && window.speechSynthesis != null
  );
}

export function speak(text: string, onEnd?: () => void): void {
  if (!isSpeechSynthesisSupported()) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  if (onEnd) utterance.onend = onEnd;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

type RecognitionResultEvent = {
  resultIndex: number;
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal?: boolean }>;
};

type RecognitionCtor = new () => {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: RecognitionResultEvent) => void) | null;
  onerror: ((event: unknown) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

function getRecognitionCtor(): RecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: RecognitionCtor;
    webkitSpeechRecognition?: RecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function isSpeechRecognitionSupported(): boolean {
  return getRecognitionCtor() !== null;
}

export function recognizeOnce(): Promise<string> {
  const Ctor = getRecognitionCtor();
  if (Ctor === null) return Promise.reject(new Error("Speech recognition is not supported"));
  return new Promise<string>((resolve, reject) => {
    const recognition = new Ctor();
    recognition.lang = "en-US";
    let settled = false;

    const timeout = setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(new Error("Speech recognition timed out"));
      }
    }, 15000);

    const finish = (fn: () => void) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      fn();
    };

    recognition.onresult = (event) => {
      const results = event.results;
      if (results.length === 0) return;
      const last = results[results.length - 1];
      if (!last.isFinal) return;
      const transcript = last[0]?.transcript.trim();
      if (transcript) {
        finish(() => resolve(transcript.toLowerCase()));
      } else {
        finish(() => reject(new Error("Speech recognition returned no transcript")));
      }
    };
    recognition.onerror = () => finish(() => reject(new Error("Speech recognition failed")));
    recognition.onend = () => {
      // If we never got a final result, reject rather than hanging forever.
      finish(() => reject(new Error("Speech recognition ended without a final result")));
    };
    recognition.start();
  });
}

export type RecognitionSession = {
  result: Promise<string>;
  stop: () => void;
};

export function startRecognition(): RecognitionSession | null {
  const Ctor = getRecognitionCtor();
  if (Ctor === null) return null;
  const recognition = new Ctor();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = true;
  const parts: string[] = [];
  let stopped = false;
  let settled = false;
  let resolveResult: (t: string) => void = () => {};
  let rejectResult: (e: Error) => void = () => {};
  const result = new Promise<string>((resolve, reject) => {
    resolveResult = resolve;
    rejectResult = reject;
  });

  const finish = (fn: () => void) => {
    if (settled) return;
    settled = true;
    fn();
  };

  recognition.onresult = (event) => {
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const item = event.results[i];
      const text = item[0]?.transcript.trim();
      if (item.isFinal && text) parts.push(text);
    }
  };
  recognition.onerror = () => finish(() => rejectResult(new Error("Speech recognition failed")));
  recognition.onend = () => {
    // Continuous recognition stays open across pauses and only ends when the
    // user stops it, so an unexpected onend means something went wrong.
    if (!stopped) {
      finish(() => rejectResult(new Error("Speech recognition ended without a result")));
    }
  };

  recognition.start();
  return {
    result,
    stop: () => {
      stopped = true;
      recognition.stop();
      finish(() => {
        const transcript = parts.join(" ").trim().toLowerCase();
        if (transcript) resolveResult(transcript);
        else rejectResult(new Error("Speech recognition returned no transcript"));
      });
    },
  };
}
