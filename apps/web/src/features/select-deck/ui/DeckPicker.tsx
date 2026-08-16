import { useState } from "react";
import { DeckSelect, useCreateDeck, useDecks } from "@/entities/deck";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";

export function DeckPicker({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (id: number) => void;
}) {
  const { t } = useI18n();
  const decks = useDecks();
  const createDeck = useCreateDeck();
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      const deck = await createDeck.mutateAsync(name.trim());
      setName("");
      setCreating(false);
      onChange(deck.id);
    } catch {
      // Surfaced to the user via createDeck.isError below; nothing further to do here.
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {decks.data && <DeckSelect decks={decks.data} value={value} onChange={onChange} />}
      {creating ? (
        <div className="flex flex-col gap-2">
          <Input
            className="w-full"
            placeholder={t("header.newDeck")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void handleCreate();
              }
            }}
          />
          <div className="flex gap-2">
            <Button
              onClick={() => void handleCreate()}
              disabled={createDeck.isPending}
              className="flex-1"
            >
              {t("header.create")}
            </Button>
            <Button variant="ghost" onClick={() => setCreating(false)}>
              ✕
            </Button>
          </div>
          {createDeck.isError && <p role="alert">{t("header.deckCreateError")}</p>}
        </div>
      ) : (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCreating(true)}
          className="justify-start text-muted-foreground"
        >
          + {t("header.newDeck")}
        </Button>
      )}
    </div>
  );
}
