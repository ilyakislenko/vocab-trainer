import { useQueries } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useCurriculumMap } from "@/entities/curriculum";
import { useDecks } from "@/entities/deck";
import { useProgress } from "@/entities/progress";
import { statsKeys } from "@/entities/stats";
import { apiClient, type Stats } from "@/shared/api";
import { formatCount } from "@/shared/lib/format";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";

async function fetchStats(deckId: number): Promise<Stats> {
  const { data, error } = await apiClient.GET("/stats", {
    params: { query: { deck_id: deckId } },
  });
  if (error) throw new Error("Failed to load stats");
  return data;
}

export function ProfilePage({ deckId }: { deckId: number | null }) {
  const { t, locale } = useI18n();
  const progress = useProgress();
  const map = useCurriculumMap();
  const decks = useDecks();
  const deckIds = (decks.data ?? [])
    .map((deck) => deck.id)
    .filter((id): id is number => id !== null);

  const stats = useQueries({
    queries: deckIds.map((deckId) => ({
      queryKey: statsKeys.byDeck(deckId),
      queryFn: () => fetchStats(deckId),
      enabled: deckIds.length > 0,
    })),
  });

  const totals = stats.reduce(
    (acc, query) => {
      const s = query.data;
      if (!s) return acc;
      return {
        reviews: acc.reviews + s.total_reviews,
        streak: Math.max(acc.streak, s.streak),
        fresh: acc.fresh + s.fsrs_new,
        learning: acc.learning + s.fsrs_learning,
        review: acc.review + s.fsrs_review,
        relearning: acc.relearning + s.fsrs_relearning,
      };
    },
    { reviews: 0, streak: 0, fresh: 0, learning: 0, review: 0, relearning: 0 },
  );

  const level = map.data?.placement_level ?? null;
  const [name, setName] = useState(() => {
    try {
      return localStorage.getItem("vt_name") ?? "";
    } catch {
      return "";
    }
  });

  const saveName = () => {
    try {
      localStorage.setItem("vt_name", name.trim());
    } catch {}
  };

  const stateRows = [
    { label: "profile.stateNew", value: totals.fresh },
    { label: "profile.stateLearning", value: totals.learning },
    { label: "profile.stateReview", value: totals.review },
    { label: "profile.stateRelearning", value: totals.relearning },
  ];

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <header>
        <h2 className="text-2xl font-black tracking-tight text-foreground">{t("profile.title")}</h2>
      </header>

      {deckId === null && <p className="text-muted-foreground">{t("profile.noDeck")}</p>}

      <section className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
        <div className="flex items-center gap-3">
          <label className="w-40 text-sm font-extrabold" htmlFor="profile-name">
            {t("profile.displayName")}
          </label>
          <Input
            id="profile-name"
            className="flex-1 rounded-full"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <Button onClick={saveName} className="rounded-full">
            {t("profile.saveName")}
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-tint-lavender px-4 py-2 text-sm font-extrabold">
            {t("profile.level")}: {level ?? t("profile.levelNotAssessed")}
          </span>
          {!level && (
            <Link to="/placement">
              <Button variant="outline" className="rounded-full">
                {t("profile.takePlacement")}
              </Button>
            </Link>
          )}
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1 rounded-3xl border border-border bg-card p-6">
          <span className="text-2xl font-black tabular-nums">
            {formatCount(totals.streak, locale)}
          </span>
          <span className="text-sm font-bold text-muted-foreground">{t("profile.streak")}</span>
        </div>
        <div className="flex flex-col gap-1 rounded-3xl border border-border bg-card p-6">
          <span className="text-2xl font-black tabular-nums">
            {formatCount(totals.reviews, locale)}
          </span>
          <span className="text-sm font-bold text-muted-foreground">
            {t("profile.totalReviews")}
          </span>
        </div>
      </section>

      <section className="rounded-3xl border border-border bg-card p-6">
        <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
          {t("profile.cardsByState")}
        </h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {stateRows.map((row) => (
            <span
              key={row.label}
              className="rounded-full bg-tint-blue px-4 py-2 text-sm font-extrabold"
            >
              {t(row.label)}: {formatCount(row.value, locale)}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-border bg-card p-6">
        <h3 className="text-sm font-black uppercase tracking-widest text-muted-foreground">
          {t("profile.curriculum")}
        </h3>
        <p className="mt-2 text-2xl font-black tabular-nums">
          {progress.data?.overall_percent ?? 0}%
        </p>
        <div className="mt-4 flex flex-col gap-2">
          {(progress.data?.levels ?? []).map((levelRow) => {
            const percent = levelRow.total > 0 ? (levelRow.completed / levelRow.total) * 100 : 0;
            return (
              <div key={levelRow.level} className="flex items-center gap-3">
                <span className="w-10 text-sm font-extrabold">{levelRow.level}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-2 rounded-full bg-primary transition-all"
                    style={{ width: `${percent}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {formatCount(levelRow.completed, locale)}/{formatCount(levelRow.total, locale)}
                </span>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
