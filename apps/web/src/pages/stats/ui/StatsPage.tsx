import { StatsPanel } from "@/widgets/stats-panel";

export function StatsPage({ deckId }: { deckId: number | null }) {
  if (deckId === null)
    return <p className="text-muted-foreground">Create a deck above to see its stats.</p>;
  return <StatsPanel deckId={deckId} />;
}
