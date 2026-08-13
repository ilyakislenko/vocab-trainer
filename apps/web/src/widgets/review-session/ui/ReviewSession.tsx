import { useState } from "react";
import { CardFace, useReviewQueue } from "@/entities/card";
import { RatingBar, useRecordReview } from "@/features/rate-card";
import type { Rating } from "@/shared/api";
import { Button } from "@/shared/ui/button";

export function ReviewSession({ deckId }: { deckId: number }) {
  const queue = useReviewQueue(deckId);
  const record = useRecordReview(deckId);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);

  if (queue.isLoading) return <p>Loading…</p>;
  const cards = queue.data ?? [];
  const card = cards[index];

  if (!card) {
    return <p className="text-lg text-muted-foreground">You're all caught up 🎉</p>;
  }

  const rate = async (rating: Rating) => {
    if (card.id === null) return;
    await record.mutateAsync({ cardId: card.id, rating });
    setRevealed(false);
    setIndex((i) => i + 1);
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <p className="text-sm text-muted-foreground">
        {index + 1} / {cards.length}
      </p>
      <CardFace card={card} revealed={revealed} />
      {revealed ? (
        <RatingBar onRate={rate} disabled={record.isPending} />
      ) : (
        <Button onClick={() => setRevealed(true)}>Show answer</Button>
      )}
    </div>
  );
}
