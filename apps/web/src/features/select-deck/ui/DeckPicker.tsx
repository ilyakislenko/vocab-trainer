import { useState } from "react";
import { DeckSelect, useCreateDeck, useDecks } from "@/entities/deck";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";

export function DeckPicker({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (id: number) => void;
}) {
  const decks = useDecks();
  const createDeck = useCreateDeck();
  const [name, setName] = useState("");

  const handleCreate = async () => {
    if (!name.trim()) return;
    const deck = await createDeck.mutateAsync(name.trim());
    setName("");
    if (deck.id !== null) onChange(deck.id);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {decks.data && <DeckSelect decks={decks.data} value={value} onChange={onChange} />}
      <Input
        className="w-40"
        placeholder="New deck…"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <Button onClick={handleCreate} disabled={createDeck.isPending}>
        Create
      </Button>
    </div>
  );
}
