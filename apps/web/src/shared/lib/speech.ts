export function isSpeechSynthesisSupported(): boolean {
  return (
    typeof window !== "undefined" && "speechSynthesis" in window && window.speechSynthesis != null
  );
}

export function speak(text: string): void {
  if (!isSpeechSynthesisSupported()) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

type RecognitionCtor = new () => {
  lang: string;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: unknown) => void) | null;
  start: () => void;
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
    recognition.onresult = (event) => {
      resolve(event.results[0][0].transcript.trim().toLowerCase());
    };
    recognition.onerror = () => reject(new Error("Speech recognition failed"));
    recognition.start();
  });
}
