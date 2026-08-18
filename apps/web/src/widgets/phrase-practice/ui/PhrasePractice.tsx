import { useState } from "react";
import {
  INTERVIEW_PHRASES,
  type PhraseCategory,
  phrasesByCategory,
} from "@/entities/interview-phrase";
import { PronounceControls } from "@/features/pronounce";
import { useI18n } from "@/shared/lib/i18n";

const CATEGORIES: PhraseCategory[] = [
  "react",
  "typescript",
  "frontend",
  "ai",
  "backend",
  "behavioral",
];

export function PhrasePractice() {
  const { t } = useI18n();
  const [category, setCategory] = useState<PhraseCategory>("react");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const phrases = phrasesByCategory(category);
  const selected = INTERVIEW_PHRASES.find((phrase) => phrase.id === selectedId) ?? null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => {
              setCategory(item);
              setSelectedId(null);
            }}
            aria-pressed={category === item}
            className={`rounded-full px-4 py-2 text-sm font-extrabold transition-colors ${
              category === item
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-tint-lavender hover:text-foreground"
            }`}
          >
            {t(`speaking.category.${item}`)}
          </button>
        ))}
      </div>

      <ul className="flex flex-col gap-2">
        {phrases.map((phrase) => (
          <li key={phrase.id}>
            <button
              type="button"
              onClick={() => setSelectedId(phrase.id)}
              aria-pressed={selectedId === phrase.id}
              className={`w-full rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition-colors ${
                selectedId === phrase.id
                  ? "border-primary bg-tint-lavender text-secondary-foreground"
                  : "border-border bg-card text-foreground hover:bg-muted"
              }`}
            >
              {phrase.text}
            </button>
          </li>
        ))}
      </ul>

      {selected ? (
        <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
          <p className="text-lg font-extrabold leading-snug">{selected.text}</p>
          <PronounceControls key={selected.id} word={selected.text} />
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{t("speaking.pickPhrase")}</p>
      )}
    </div>
  );
}
