import { ReviewSession } from "@/widgets/review-session";

export function ReviewPage({ deckId }: { deckId: number | null }) {
  if (deckId === null)
    return (
      <p className="text-muted-foreground">
        No decks yet — create one with the “New deck…” box above to get started.
      </p>
    );
  // Key on deckId so switching decks (a setState in the always-mounted header
  // DeckPicker, not a route change) fully remounts the session and resets its
  // snapshotted queue/index/revealed state instead of reusing stale state.
  return <ReviewSession key={deckId} deckId={deckId} />;
}
