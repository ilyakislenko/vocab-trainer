import { Flame } from "lucide-react";
import { useProgress } from "@/entities/progress";
import { formatCount } from "@/shared/lib/format";
import { useI18n } from "@/shared/lib/i18n";

const LEVEL_LABEL_KEYS: Record<string, string> = {
  A1: "learn.levelA1",
  A2: "learn.levelA2",
  B1: "learn.levelB1",
  B2: "learn.levelB2",
  C1: "learn.levelC1",
  C2: "learn.levelC2",
};

export function ProgressDashboard() {
  const { t, locale } = useI18n();
  const report = useProgress();

  if (report.isLoading) {
    return <p className="text-sm font-bold text-muted-foreground">{t("progress.loading")}</p>;
  }
  if (report.isError || !report.data) {
    return <p className="text-sm font-bold text-destructive">{t("progress.error")}</p>;
  }

  const { levels, overall_percent, streak } = report.data;

  return (
    <section className="rounded-3xl border border-border bg-card p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-black tracking-tight text-foreground">
            {t("progress.title")}
          </h3>
          <p className="text-sm font-bold text-muted-foreground">{t("progress.hint")}</p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          {streak > 0 && (
            <span className="flex items-center gap-1 rounded-full bg-orange-100 px-3 py-1 text-sm font-extrabold text-orange-700">
              <Flame size={14} />
              {formatCount(streak, locale)} {t("progress.streak")}
            </span>
          )}
          <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-extrabold text-primary">
            {t("progress.overall")} · {overall_percent}%
          </span>
        </div>
      </div>

      <ul className="mt-4 flex flex-col gap-3">
        {levels.map((level) => {
          const percent = level.total > 0 ? Math.round((100 * level.completed) / level.total) : 0;
          return (
            <li key={level.level} className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="font-black tracking-tight text-foreground">
                  {t(LEVEL_LABEL_KEYS[level.level] ?? level.level)}
                </span>
                <span className="font-extrabold text-muted-foreground">
                  {formatCount(level.completed, locale)}/{formatCount(level.total, locale)} ·{" "}
                  {percent}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
