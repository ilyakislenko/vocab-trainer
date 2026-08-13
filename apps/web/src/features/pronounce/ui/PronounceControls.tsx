import { useState } from "react";
import { isSpeechRecognitionSupported, recognizeOnce, speak } from "@/shared/lib/speech";
import { Button } from "@/shared/ui/button";

type Result = { heard: string; match: boolean };

export function PronounceControls({ word }: { word: string }) {
  const [result, setResult] = useState<Result | null>(null);
  const [listening, setListening] = useState(false);
  const recognitionSupported = isSpeechRecognitionSupported();

  const record = async () => {
    setListening(true);
    setResult(null);
    try {
      const heard = await recognizeOnce();
      setResult({ heard, match: heard === word.trim().toLowerCase() });
    } catch {
      setResult({ heard: "", match: false });
    } finally {
      setListening(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => speak(word)}>
          🔊 Hear it
        </Button>
        <Button variant="outline" onClick={record} disabled={!recognitionSupported || listening}>
          🎤 Say it
        </Button>
      </div>
      {!recognitionSupported && (
        <p className="text-muted-foreground text-xs">
          Speech recognition isn't available in this browser.
        </p>
      )}
      {result && (
        <p className="text-sm">
          {result.match
            ? "✓ Nice — that matched!"
            : `✗ Heard "${result.heard || "nothing"}", try again.`}
        </p>
      )}
    </div>
  );
}
