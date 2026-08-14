import type { Deck } from "@/shared/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";

export function DeckSelect({
  decks,
  value,
  onChange,
}: {
  decks: Deck[];
  value: number | null;
  onChange: (id: number) => void;
}) {
  return (
    <Select
      value={value ? String(value) : null}
      onValueChange={(v) => {
        if (v) onChange(Number(v));
      }}
    >
      <SelectTrigger className="w-56">
        <SelectValue>
          {(selected: string | null) =>
            decks.find((d) => String(d.id) === selected)?.name ?? "Select a deck"
          }
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {decks.map((d) => (
          <SelectItem key={d.id} value={String(d.id)}>
            {d.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
