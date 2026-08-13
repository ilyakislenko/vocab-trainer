import { useEffect, useState } from "react";
import { useReviewQueue } from "@/entities/card";
import { SentencePractice } from "@/features/check-sentence";
import { PronounceControls } from "@/features/pronounce";
import type { Card } from "@/shared/api";
import { Button } from "@/shared/ui/button";

export function PracticeSession({ deckId }: { deckId: number }) {
  const queue = useReviewQueue(deckId);
  // Snapshot the queue once on first load, same as ReviewSession: a
  // background refetch must not disrupt the fixed list this session is
  // stepping through.
  const [cards, setCards] = useState<Card[] | null>(null);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (cards === null && queue.data !== undefined) setCards(queue.data);
  }, [cards, queue.data]);

  if (cards === null) return <p>Loading…</p>;
  const card = cards[index];
  if (!card) {
    return <p className="text-lg text-muted-foreground">Nothing to practise right now 🎉</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        {index + 1} / {cards.length}
      </p>
      {card.id !== null && <SentencePractice cardId={card.id} word={card.word} />}
      <PronounceControls word={card.word} />
      <Button variant="ghost" onClick={() => setIndex((i) => i + 1)}>
        Next word →
      </Button>
    </div>
  );
}
