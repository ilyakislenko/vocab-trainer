import { useState } from "react";
import type { PronunciationAssessment, WordScore } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import {
  overallPercent,
  overallScorePercent,
  type PronounceVerdict,
  verdictTone,
} from "../model/verdict";

const toneClasses: Record<PronounceVerdict, string> = {
  good: "border-emerald-500/40 bg-emerald-500/15 text-emerald-700",
  fair: "border-amber-500/40 bg-amber-500/15 text-amber-700",
  weak: "border-red-500/40 bg-red-500/15 text-red-700",
};

export function PronounceAssessment({ assessment }: { assessment: PronunciationAssessment }) {
  const { t } = useI18n();
  const [openWord, setOpenWord] = useState<string | null>(null);

  if (!assessment.scored_phonemes) {
    return <p className="text-sm text-muted-foreground">{t("pronounce.phonemeOffline")}</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <p className="text-sm font-black uppercase tracking-wider text-muted-foreground">
          {t("pronounce.overall")}
        </p>
        <span className="rounded-full bg-primary/10 px-3 py-1 text-lg font-black text-primary">
          {overallScorePercent(assessment.overall)}%
        </span>
      </div>
      <ul className="flex flex-wrap gap-2">
        {assessment.words.map((word) => (
          <WordChip
            key={word.word}
            word={word}
            open={openWord === word.word}
            onToggle={() => setOpenWord(openWord === word.word ? null : word.word)}
          />
        ))}
      </ul>
    </div>
  );
}

function WordChip({
  word,
  open,
  onToggle,
}: {
  word: WordScore;
  open: boolean;
  onToggle: () => void;
}) {
  const { t } = useI18n();
  const tone = verdictTone(word.phonemes[0]?.verdict ?? "weak");
  const weak = word.phonemes.filter((p) => p.verdict === "weak");
  return (
    <li className="flex flex-col gap-1">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className={`rounded-full border px-3 py-1 text-sm font-bold transition-colors ${toneClasses[tone]}`}
      >
        {word.word}
      </button>
      {open && (
        <div className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-3 text-sm">
          {word.phonemes.map((phoneme) => (
            <p key={phoneme.phoneme} className="text-muted-foreground">
              <span className="font-mono font-bold text-foreground">/{phoneme.phoneme}/</span>{" "}
              {t(`pronounce.verdict.${phoneme.verdict}`)} — {overallPercent(phoneme.score)}%
            </p>
          ))}
          {weak.length > 0 && (
            <p className="text-muted-foreground">
              {t("pronounce.phonemeHint").replace("{phoneme}", weak[0].phoneme)}
            </p>
          )}
        </div>
      )}
    </li>
  );
}
