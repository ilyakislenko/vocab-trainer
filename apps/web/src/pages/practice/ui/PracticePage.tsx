import { PracticeSession } from "@/widgets/practice-session";

export function PracticePage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck to practise.</p>;
  // Key on deckId so switching decks fully remounts the session and resets
  // its snapshotted queue/index state instead of reusing stale state.
  return <PracticeSession key={deckId} deckId={deckId} />;
}
