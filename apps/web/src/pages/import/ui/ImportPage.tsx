import { ImportPanel } from "@/widgets/import-panel";

export function ImportPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <p className="text-muted-foreground">Pick a deck first.</p>;
  return <ImportPanel deckId={deckId} />;
}
