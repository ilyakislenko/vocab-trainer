import { useStats } from "@/entities/stats";
import { formatCount } from "@/shared/lib/format";
import { useI18n } from "@/shared/lib/i18n";
import { Card, CardContent } from "@/shared/ui/card";

function Tile({
  label,
  value,
  icon,
  tint,
}: {
  label: string;
  value: number | string;
  icon?: string;
  tint?: string;
}) {
  return (
    <Card className={`flex-1 border-border ${tint ?? "bg-card"}`}>
      <CardContent className="py-6 text-center">
        <div className="text-3xl font-black tracking-tight">
          {icon && <span className="mr-1">{icon}</span>}
          {value}
        </div>
        <div className="mt-1 text-sm font-bold text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}

export function StatsPanel({ deckId }: { deckId: number }) {
  const { t, locale } = useI18n();
  const stats = useStats(deckId);
  if (!stats.data) return <p>{t("common.loading")}</p>;

  const maxActivity = Math.max(...stats.data.activity.map((a) => Number(a.count)), 1);
  const count = (n: number) => formatCount(n, locale);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-3">
        <Tile
          label={t("stats.dueToday")}
          value={count(stats.data.due_today)}
          icon="📅"
          tint="bg-tint-lavender"
        />
        <Tile
          label={t("stats.totalReviews")}
          value={count(stats.data.total_reviews)}
          icon="📊"
          tint="bg-tint-blue"
        />
        <Tile
          label={t("stats.streak")}
          value={`${count(stats.data.streak)}🔥`}
          icon=""
          tint="bg-tint-peach"
        />
      </div>

      {/* FSRS breakdown */}
      <div className="rounded-3xl border border-border bg-card p-4">
        <p className="mb-3 text-xs font-black uppercase tracking-wider text-primary">
          {t("stats.cardsByState")}
        </p>
        <div className="flex flex-wrap gap-2 text-sm">
          <span className="rounded-full bg-tint-lavender px-3 py-1 font-extrabold text-secondary-foreground">
            🆕 {t("stats.new")}: <b>{count(stats.data.fsrs_new)}</b>
          </span>
          <span className="rounded-full bg-tint-blue px-3 py-1 font-extrabold text-secondary-foreground">
            📖 {t("stats.learning")}: <b>{count(stats.data.fsrs_learning)}</b>
          </span>
          <span className="rounded-full bg-tint-lavender px-3 py-1 font-extrabold text-secondary-foreground">
            ✅ {t("stats.review")}: <b>{count(stats.data.fsrs_review)}</b>
          </span>
          <span className="rounded-full bg-tint-peach px-3 py-1 font-extrabold text-secondary-foreground">
            🔄 {t("stats.relearning")}: <b>{count(stats.data.fsrs_relearning)}</b>
          </span>
        </div>
      </div>

      {/* Activity chart */}
      {stats.data.activity.length > 0 && (
        <div className="rounded-3xl border border-border bg-card p-4">
          <p className="mb-2 text-xs font-black uppercase tracking-wider text-primary">
            {t("stats.last7Days")}
          </p>
          <div className="flex items-end gap-1">
            {stats.data.activity.map((a) => (
              <div key={String(a.date)} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t-lg bg-primary transition-all"
                  style={{ height: `${(Number(a.count) / maxActivity) * 64}px`, minHeight: 4 }}
                />
                <span className="text-xs text-muted-foreground">{String(a.date).slice(5)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
