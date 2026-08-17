import { ImportPanel } from "@/widgets/import-panel";
import { NoDeck } from "@/widgets/no-deck";

export function ImportPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <NoDeck />;
  return <ImportPanel deckId={deckId} />;
}
