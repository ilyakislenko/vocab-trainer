import { StatsPanel } from "@/widgets/stats-panel";

export function StatsPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck first.</p>;
  return <StatsPanel deckId={deckId} />;
}
