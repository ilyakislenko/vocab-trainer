import { ReviewSession } from "@/widgets/review-session";

export function ReviewPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck to start.</p>;
  return <ReviewSession deckId={deckId} />;
}
