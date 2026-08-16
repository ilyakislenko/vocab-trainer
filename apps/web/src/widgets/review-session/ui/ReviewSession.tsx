import { useEffect, useState } from "react";
import { toast } from "sonner";
import { CardFace, useReviewQueue } from "@/entities/card";
import { RatingBar, useRecordReview } from "@/features/rate-card";
import type { Card, Rating } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";

const RATING_NAME_KEYS: Record<Rating, string> = {
  1: "review.ratingAgain",
  2: "review.ratingHard",
  3: "review.ratingGood",
  4: "review.ratingEasy",
};

export function ReviewSession({ deckId }: { deckId: number }) {
  const { t } = useI18n();
  const queue = useReviewQueue(deckId);
  const record = useRecordReview(deckId);
  const [sessionCards, setSessionCards] = useState<Card[] | null>(null);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [ratings, setRatings] = useState<Record<Rating, number>>({ 1: 0, 2: 0, 3: 0, 4: 0 });
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    if (sessionCards === null && queue.data !== undefined) {
      setSessionCards(queue.data);
    }
  }, [queue.data, sessionCards]);

  if (sessionCards === null) return <p>{t("practice.loading")}</p>;
  const card = sessionCards[index];

  if (!card || complete) {
    return (
      <div className="flex flex-col items-center gap-6 rounded-3xl border border-border bg-card p-8 text-center">
        <span className="text-5xl">🎉</span>
        <p className="text-2xl font-black tracking-tight">{t("review.summary")}</p>
        <p className="text-muted-foreground">
          {t("review.reviewed")}: {index}
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
            setIndex(0);
            setRatings({ 1: 0, 2: 0, 3: 0, 4: 0 });
            setRevealed(false);
            setComplete(false);
          }}
          className="rounded-full"
        >
          {t("review.startAgain")}
        </Button>
      </div>
    );
  }

  const progress = sessionCards.length > 0 ? ((index + 1) / sessionCards.length) * 100 : 0;

  const rate = async (rating: Rating) => {
    if (card.id === null) return;
    try {
      await record.mutateAsync({ cardId: card.id, rating });
      setRatings((prev) => ({ ...prev, [rating]: prev[rating] + 1 }));
      setRevealed(false);
      setIndex((i) => i + 1);
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
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-sm text-muted-foreground tabular-nums">
          {index + 1} / {sessionCards.length}
        </span>
      </div>

      <CardFace card={card} revealed={revealed} />
      {revealed ? (
        <RatingBar onRate={rate} disabled={record.isPending} />
      ) : (
        <Button onClick={() => setRevealed(true)} className="rounded-full px-8">
          {t("review.showAnswer")}
        </Button>
      )}
    </div>
  );
}
