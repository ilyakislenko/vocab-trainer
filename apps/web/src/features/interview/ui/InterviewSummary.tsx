import { CheckCircle2, Clock, ListChecks, RotateCcw, TriangleAlert } from "lucide-react";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { type Emotion, Mascot } from "@/shared/ui/mascot";
import type { SessionStats } from "../model/use-interview-session";

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function InterviewSummary({
  stats,
  elapsed,
  onRestart,
  onBack,
}: {
  stats: SessionStats;
  elapsed: number;
  onRestart: () => void;
  onBack: () => void;
}) {
  const { t } = useI18n();
  const emotion: Emotion =
    stats.ok >= stats.needsWork && stats.needsWork === 0
      ? "happy"
      : stats.needsWork > stats.ok
        ? "sad"
        : "idle";

  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center gap-4">
        <Mascot emotion={emotion} className="h-16 w-16" />
        <div>
          <h3 className="text-xl font-black tracking-tight">{t("interview.summaryTitle")}</h3>
          <p className="text-sm text-muted-foreground">{t("interview.summarySubtitle")}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-center">
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-300">
            {stats.ok}
          </div>
          <div className="text-xs font-semibold text-muted-foreground">{t("interview.ok")}</div>
        </div>
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-center">
          <div className="text-2xl font-black text-amber-600 dark:text-amber-300">
            {stats.needsWork}
          </div>
          <div className="text-xs font-semibold text-muted-foreground">
            {t("interview.needsWork")}
          </div>
        </div>
        <div className="rounded-xl border border-border bg-muted/40 p-3 text-center">
          <div className="text-2xl font-black text-foreground">{stats.questions}</div>
          <div className="text-xs font-semibold text-muted-foreground">
            {t("interview.questions")}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Clock className="size-4" />
        <span>
          {t("interview.duration")}: {formatTime(elapsed)}
        </span>
      </div>

      {stats.corrections.length > 0 ? (
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 text-sm font-bold text-foreground">
            <ListChecks className="size-4" />
            {t("interview.corrections")}
          </div>
          <ul className="flex flex-col gap-2">
            {stats.corrections.map((correction) => (
              <li
                key={correction}
                className="flex items-start gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm"
              >
                <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-amber-500" />
                <span>{correction}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700 dark:text-emerald-300">
          <CheckCircle2 className="size-4 shrink-0" />
          {t("interview.noCorrections")}
        </div>
      )}

      <div className="flex gap-3">
        <Button onClick={onRestart} size="lg">
          <RotateCcw className="size-4" />
          {t("interview.startAgain")}
        </Button>
        <Button variant="outline" size="lg" onClick={onBack}>
          {t("interview.backToSetup")}
        </Button>
      </div>
    </div>
  );
}
