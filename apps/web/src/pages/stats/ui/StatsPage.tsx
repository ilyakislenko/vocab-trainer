import { NoDeck } from "@/widgets/no-deck";
import { StatsPanel } from "@/widgets/stats-panel";

export function StatsPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <NoDeck />;
  return <StatsPanel deckId={deckId} />;
}
