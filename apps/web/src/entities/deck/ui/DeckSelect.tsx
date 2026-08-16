import type { Deck } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
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
  const { t } = useI18n();
  return (
    <Select
      value={value ? String(value) : null}
      onValueChange={(v) => {
        if (v) onChange(Number(v));
      }}
    >
      <SelectTrigger className="w-full">
        <SelectValue>
          {(selected: string | null) =>
            decks.find((d) => String(d.id) === selected)?.name ?? t("header.selectDeck")
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
