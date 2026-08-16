import { useRef, useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import {
  isSpeechRecognitionSupported,
  type RecognitionSession,
  recognizeOnce,
  startRecognition,
} from "@/shared/lib/speech";
import { Button } from "@/shared/ui/button";

export function MicButton({
  onTranscript,
  onError,
  disabled,
  className,
  ariaLabel,
  label,
  continuous = false,
  onListeningChange,
}: {
  onTranscript: (transcript: string) => void;
  onError?: () => void;
  disabled?: boolean;
  className?: string;
  ariaLabel?: string;
  label?: string;
  continuous?: boolean;
  onListeningChange?: (listening: boolean) => void;
}) {
  const { t } = useI18n();
  const [listening, setListening] = useState(false);
  const sessionRef = useRef<RecognitionSession | null>(null);

  if (!isSpeechRecognitionSupported()) return null;

  const setListeningState = (next: boolean) => {
    setListening(next);
    onListeningChange?.(next);
  };

  const record = async () => {
    if (continuous) {
      if (listening) {
        const session = sessionRef.current;
        sessionRef.current = null;
        setListeningState(false);
        if (!session) return;
        session.stop();
        try {
          onTranscript(await session.result);
        } catch {
          onError?.();
        }
        return;
      }
      const session = startRecognition();
      if (!session) return;
      sessionRef.current = session;
      setListeningState(true);
      return;
    }
    setListeningState(true);
    try {
      const transcript = await recognizeOnce();
      onTranscript(transcript);
    } catch {
      onError?.();
    } finally {
      setListeningState(false);
    }
  };

  return (
    <Button
      variant="outline"
      onClick={record}
      disabled={disabled || (continuous ? false : listening)}
      className={listening ? `${className ?? ""} animate-pulse text-red-500`.trim() : className}
      aria-label={
        label
          ? undefined
          : listening && continuous
            ? t("practice.stopRecording")
            : (ariaLabel ?? t("practice.voiceInput"))
      }
    >
      {label ?? (listening && continuous ? "⏹" : "🎤")}
    </Button>
  );
}
