import { useEffect, useState } from "react";
import { toast } from "sonner";
import { CardFace, useReviewQueue, useReviewSummary } from "@/entities/card";
import { RatingBar, useRecordReview } from "@/features/rate-card";
import type { Card, Rating } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { useRevealShortcut } from "@/shared/lib/use-reveal-shortcut";
import { Button } from "@/shared/ui/button";

const RATING_NAME_KEYS: Record<Rating, string> = {
  1: "review.ratingAgain",
  2: "review.ratingHard",
  3: "review.ratingGood",
  4: "review.ratingEasy",
};

const DAY_MS = 86_400_000;

function duePhrase(t: (key: string) => string, due: string | null | undefined): string | null {
  if (!due) return null;
  const days = Math.max(0, Math.ceil((new Date(due).getTime() - Date.now()) / DAY_MS));
  if (days <= 1) return t("review.returnsTomorrow");
  return t("review.returnsIn").replace("{n}", String(days));
}

export function ReviewSession({ deckId }: { deckId: number }) {
  const { t } = useI18n();
  const queue = useReviewQueue(deckId);
  const record = useRecordReview(deckId);
  const [plan, setPlan] = useState<Card[] | null>(null);
  const [remaining, setRemaining] = useState<Card[]>([]);
  const [revealed, setRevealed] = useState(false);
  const [ratings, setRatings] = useState<Record<Rating, number>>({ 1: 0, 2: 0, 3: 0, 4: 0 });

  useEffect(() => {
    if (plan === null && queue.data !== undefined) {
      setPlan(queue.data);
      setRemaining(queue.data);
    }
  }, [queue.data, plan]);

  const done = plan !== null && remaining.length === 0;
  const summary = useReviewSummary(deckId, done);

  useRevealShortcut(!revealed && !done, () => setRevealed(true));

  if (plan === null) return <p>{t("practice.loading")}</p>;

  if (done) {
    const nextDue = summary.data?.next_due ?? null;
    const returnsIn = duePhrase(t, nextDue);
    return (
      <div className="flex flex-col items-center gap-6 rounded-3xl border border-border bg-card p-8 text-center">
        <span className="text-5xl">🎉</span>
        <p className="text-2xl font-black tracking-tight">{t("review.summary")}</p>
        {returnsIn ? (
          <p className="text-muted-foreground">{returnsIn}</p>
        ) : (
          <p className="text-muted-foreground">{t("review.caughtUp")}</p>
        )}
        <p className="text-muted-foreground">
          {plan.length} {t("review.reviewed")} · {summary.data?.reviewed_today ?? 0}{" "}
          {t("review.reviewedToday")}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {([1, 2, 3, 4] as Rating[]).map((r) => (
            <span
              key={r}
              className="rounded-full bg-tint-lavender px-3 py-1 text-sm font-extrabold text-secondary-foreground"
            >
              {t(RATING_NAME_KEYS[r])}: {ratings[r]}
            </span>
          ))}
        </div>
        <Button
          onClick={() => {
            setRatings({ 1: 0, 2: 0, 3: 0, 4: 0 });
            setRevealed(false);
            setPlan(null);
            setRemaining([]);
            void queue.refetch();
          }}
          className="rounded-full"
        >
          {t("review.practiceMore")}
        </Button>
      </div>
    );
  }

  const card = remaining[0];
  if (!card) return null;

  const progress = plan.length > 0 ? ((plan.length - remaining.length) / plan.length) * 100 : 0;

  const rate = async (rating: Rating) => {
    if (card.id === null) return;
    try {
      await record.mutateAsync({ cardId: card.id, rating });
      setRatings((prev) => ({ ...prev, [rating]: prev[rating] + 1 }));
      setRevealed(false);
      setRemaining((prev) => {
        const rest = prev.slice(1);
        // A2: "Again" keeps the card in this session — it goes to the back of the queue.
        return rating === 1 ? [...rest, card] : rest;
      });
    } catch {
      toast.error(t("feedback.unavailable"));
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Progress bar */}
      <div className="flex w-full max-w-md items-center gap-3">
        <div className="flex-1 overflow-hidden rounded-full bg-muted">
          <div
            className="h-2 rounded-full bg-primary transition-all"
            style={{ width: `${Math.min(100, progress)}%` }}
          />
        </div>
        <span className="text-sm text-muted-foreground tabular-nums">
          {remaining.length} {t("review.left")}
        </span>
      </div>

      <CardFace card={card} revealed={revealed} />
      {revealed ? (
        <>
          {duePhrase(t, card.due) && (
            <p className="text-sm text-muted-foreground">{duePhrase(t, card.due)}</p>
          )}
          <RatingBar onRate={rate} disabled={record.isPending} />
        </>
      ) : (
        <Button onClick={() => setRevealed(true)} className="rounded-full px-8">
          {t("review.showAnswer")}
          <span className="ml-2 opacity-60">{t("review.revealHint")}</span>
        </Button>
      )}
    </div>
  );
}
