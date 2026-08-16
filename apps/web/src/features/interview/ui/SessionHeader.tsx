import { PhoneOff, Timer } from "lucide-react";
import { useI18n } from "@/shared/lib/i18n";
import { cn } from "@/shared/lib/utils";
import type { SessionStats } from "../model/use-interview-session";

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function SessionHeader({
  topic,
  stats,
  elapsed,
  onEnd,
  onRestart,
  className,
}: {
  topic: string;
  stats: SessionStats;
  elapsed: number;
  onEnd: () => void;
  onRestart: () => void;
  className?: string;
}) {
  const { t } = useI18n();
  const total = stats.questions;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-card px-4 py-3",
        className,
      )}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg">{topic}</span>
        <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-bold text-primary">
          {t("interview.sessionQuestion").replace("{n}", String(total))}
        </span>
      </div>

      <div className="ml-auto flex items-center gap-2 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 font-semibold">
          <Timer className="size-3.5" />
          {formatTime(elapsed)}
        </span>
        <button
          type="button"
          onClick={onRestart}
          className="rounded-full border border-border bg-background px-3 py-1 text-xs font-semibold text-muted-foreground transition hover:text-foreground"
        >
          {t("interview.restart")}
        </button>
        <button
          type="button"
          onClick={onEnd}
          className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-3 py-1 text-xs font-bold text-destructive transition hover:bg-destructive/20"
        >
          <PhoneOff className="size-3.5" />
          {t("interview.finish")}
        </button>
      </div>
    </div>
  );
}
