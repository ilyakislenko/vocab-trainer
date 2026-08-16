import { ImportForm } from "@/features/import-words";

export function ImportPanel({ deckId }: { deckId: number }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-xs font-black uppercase tracking-widest text-primary">Import words</h2>
      <ImportForm deckId={deckId} />
    </section>
  );
}
