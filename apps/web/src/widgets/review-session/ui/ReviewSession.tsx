import { useEffect, useState } from "react";
import { CardFace, useReviewQueue } from "@/entities/card";
import { RatingBar, useRecordReview } from "@/features/rate-card";
import type { Card, Rating } from "@/shared/api";
import { Button } from "@/shared/ui/button";

export function ReviewSession({ deckId }: { deckId: number }) {
  const queue = useReviewQueue(deckId);
  const record = useRecordReview(deckId);
  // Snapshot the queue once on first load. The mutation invalidates the live
  // query on success (so other views refetch), but the active session must
  // keep advancing over the fixed list it started with — otherwise a
  // shorter refetched queue (FSRS pushed a card's due date into the future)
  // would overrun the local index and silently skip the next due card.
  const [sessionCards, setSessionCards] = useState<Card[] | null>(null);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    if (sessionCards === null && queue.data !== undefined) {
      setSessionCards(queue.data);
    }
  }, [queue.data, sessionCards]);

  if (sessionCards === null) return <p>Loading…</p>;
  const card = sessionCards[index];

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
        {index + 1} / {sessionCards.length}
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
