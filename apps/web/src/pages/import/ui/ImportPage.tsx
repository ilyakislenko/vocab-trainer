import { ImportPanel } from "@/widgets/import-panel";

export function ImportPage({ deckId }: { deckId: number | null }) {
  if (deckId === null)
    return (
      <p className="text-muted-foreground">
        Create a deck first — use the “New deck…” box above — then import words into it here.
      </p>
    );
  return <ImportPanel deckId={deckId} />;
}
