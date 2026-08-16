import { lazy, Suspense } from "react";
import { cn } from "@/shared/lib/utils";
import type { Emotion } from "./lottie-mascot";

const LottieMascot = lazy(() =>
  import("./lottie-mascot").then((m) => ({ default: m.LottieMascot })),
);

const EMOTION_LABELS: Record<Emotion, string> = {
  happy: "Ура!",
  sad: "Попробуй ещё!",
  thinking: "Хмм...",
  listening: "Слушаю...",
  speaking: "Говорю...",
  idle: "",
};

function isTestEnvironment(): boolean {
  return typeof navigator !== "undefined" && /jsdom/.test(navigator.userAgent);
}

export type { Emotion } from "./lottie-mascot";

export function Mascot({ emotion = "idle", className }: { emotion?: Emotion; className?: string }) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-1", className)}
      role="img"
      aria-label={EMOTION_LABELS[emotion]}
    >
      {isTestEnvironment() ? (
        <SvgFallback />
      ) : (
        <Suspense fallback={<SvgFallback />}>
          <LottieMascot emotion={emotion} />
        </Suspense>
      )}
    </div>
  );
}

function SvgFallback() {
  return (
    <svg viewBox="0 0 700 700" className="h-full w-full" role="img" aria-hidden="true">
      <title>Робот</title>
      <circle cx="350" cy="350" r="220" fill="#7C848F" />
      <circle cx="350" cy="350" r="150" fill="#E4E7EB" />
      <circle cx="280" cy="320" r="30" fill="#2A2D33" />
      <circle cx="420" cy="320" r="30" fill="#2A2D33" />
      <rect x="330" y="380" width="40" height="70" rx="10" fill="#2A2D33" />
    </svg>
  );
}
