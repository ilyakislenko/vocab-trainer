import { useEffect, useState } from "react";
import { playError, playSuccess } from "@/shared/lib/sounds";
import { cn } from "@/shared/lib/utils";
import type { Emotion } from "@/shared/ui/mascot";
import { Mascot } from "@/shared/ui/mascot";

const PHRASES: Record<"success" | "error", string[]> = {
  success: [
    "Отлично! 🎉",
    "Супер! Ты молодец!",
    "Браво! Так держать!",
    "Великолепно!",
    "Ты отлично справляешься!",
    "Потрясающе!",
    "Так и надо! 💪",
    "В точку!",
  ],
  error: [
    "Не переживай, попробуй ещё!",
    "Ты справишься! 💪",
    "Практика делает мастера!",
    "Почти! Давай ещё раз!",
    "Не сдавайся!",
    "С каждой попыкой ты лучше!",
    "Это нормально — ошибки это учёба!",
    "В следующий раз точно получится!",
  ],
};

type Verdict = "ok" | "needs_work" | "idle";

export function PracticeFeedback({ verdict }: { verdict: Verdict }) {
  const [phrase, setPhrase] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (verdict === "idle") {
      setPhrase(null);
      setVisible(false);
      return;
    }

    const phrases = PHRASES[verdict === "ok" ? "success" : "error"];
    setPhrase(phrases[Math.floor(Math.random() * phrases.length)]);
    setVisible(true);

    // Play sound
    if (verdict === "ok") playSuccess();
    else playError();
  }, [verdict]);

  if (verdict === "idle" || !visible || !phrase) return null;

  const emotion: Emotion = verdict === "ok" ? "happy" : "sad";
  const bgColor =
    verdict === "ok" ? "bg-green-50 border-green-200" : "bg-amber-50 border-amber-200";
  const textColor = verdict === "ok" ? "text-green-700" : "text-amber-700";

  return (
    <div className={cn("flex items-center gap-3 rounded-2xl border p-4", bgColor)}>
      <Mascot emotion={emotion} />
      <div className="flex flex-col">
        <span className={cn("text-lg font-extrabold", textColor)}>
          {verdict === "ok" ? "Правильно!" : "Нужно подучить"}
        </span>
        <span className="text-sm text-muted-foreground">{phrase}</span>
      </div>
    </div>
  );
}
