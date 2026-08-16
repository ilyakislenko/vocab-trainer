import type { LottieHandle } from "lottie-react";
import { LottieSvg } from "lottie-react";
import { useEffect, useRef } from "react";
import { aiRobo } from "@/shared/assets";

export type Emotion = "happy" | "sad" | "thinking" | "idle" | "listening" | "speaking";

const STATE_SEGMENTS: Record<Emotion, [number, number]> = {
  idle: [0, 29],
  happy: [391, 479],
  sad: [106, 180],
  listening: [31, 105],
  thinking: [271, 390],
  speaking: [181, 270],
};

export function LottieMascot({ emotion }: { emotion: Emotion }) {
  const lottieRef = useRef<LottieHandle>(null);

  useEffect(() => {
    const segment = STATE_SEGMENTS[emotion];
    lottieRef.current?.playSegments(segment);
  }, [emotion]);

  return (
    <LottieSvg
      src={aiRobo}
      loop
      lottieRef={lottieRef}
      className="h-full w-full"
      role="presentation"
    />
  );
}
