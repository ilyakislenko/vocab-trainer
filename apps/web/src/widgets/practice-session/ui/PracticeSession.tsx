import { useCallback, useEffect, useState } from "react";
import { SentencePractice } from "@/features/check-sentence";
import { DrillChat } from "@/features/drill-word";
import { PracticeFeedback } from "@/features/practice-feedback";
import { PronounceControls } from "@/features/pronounce";
import { WordHintTooltip } from "@/features/word-hint";
import type { Card } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { SpeakButton } from "@/shared/ui/speak-button";

type Tab = "sentence" | "pronounce" | "drill";

const TABS: { key: Tab; icon: string; labelKey: string }[] = [
  { key: "sentence", icon: "✏️", labelKey: "practice.tabSentence" },
  { key: "pronounce", icon: "🎤", labelKey: "practice.tabSpeak" },
  { key: "drill", icon: "💬", labelKey: "practice.tabDrill" },
];

export function PracticeSession({
  cards,
  isLoading,
}: {
  cards: Card[] | undefined;
  isLoading: boolean;
}) {
  const { t } = useI18n();
  const [snapshot, setSnapshot] = useState<Card[] | null>(null);
  const [index, setIndex] = useState(0);
  const [verdict, setVerdict] = useState<"ok" | "needs_work" | "idle">("idle");
  const [pronounceVerdict, setPronounceVerdict] = useState<"ok" | "needs_work" | "idle">("idle");
  const [drillOpen, setDrillOpen] = useState(false);
  const [tab, setTab] = useState<Tab>("sentence");

  useEffect(() => {
    if (snapshot === null && cards !== undefined) setSnapshot(cards);
  }, [snapshot, cards]);

  const handleFeedback = useCallback((v: "ok" | "needs_work") => {
    setVerdict(v);
  }, []);

  const handlePronounceResult = useCallback((matched: boolean) => {
    setPronounceVerdict(matched ? "ok" : "needs_work");
  }, []);

  const currentCardId = snapshot?.[index]?.id;
  useEffect(() => {
    void currentCardId;
    setVerdict("idle");
    setPronounceVerdict("idle");
    setDrillOpen(false);
  }, [currentCardId]);

  if (isLoading && snapshot === null) return <p>{t("practice.loading")}</p>;
  const card = snapshot?.[index];
  if (!card) {
    return <p className="text-lg text-muted-foreground">{t("practice.nothing")}</p>;
  }

  const progress = snapshot.length > 0 ? ((index + 1) / snapshot.length) * 100 : 0;

  return (
    <div className="flex flex-col gap-4">
      {/* Progress bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 overflow-hidden rounded-full bg-muted">
          <div
            className="h-2 rounded-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-sm text-muted-foreground tabular-nums">
          {index + 1} / {snapshot.length}
        </span>
      </div>

      {/* Word card */}
      <div className="rounded-3xl border border-border bg-tint-lavender p-6 text-center">
        <div className="flex items-center justify-center gap-2">
          {card.id !== null ? (
            <WordHintTooltip cardId={card.id}>
              <span className="text-4xl font-black tracking-tight">{card.word}</span>
            </WordHintTooltip>
          ) : (
            <span className="text-4xl font-black tracking-tight">{card.word}</span>
          )}
          <SpeakButton
            text={card.word}
            variant="ghost"
            size="icon"
            className="rounded-full bg-white text-lg hover:bg-white/80"
          />
        </div>
        {card.transcription && <p className="mt-1 text-muted-foreground">/{card.transcription}/</p>}
        <p className="mt-2 text-xl font-extrabold text-foreground/80">{card.translation}</p>
        {card.section && (
          <span className="mt-3 inline-block rounded-full bg-white px-3 py-1 text-xs font-black text-primary">
            {card.section}
          </span>
        )}
      </div>

      {/* Tabs */}
      {card.id !== null && (
        <div className="flex gap-1 rounded-2xl border border-border bg-card p-1">
          {TABS.map(({ key, icon, labelKey }) => (
            <button
              key={key}
              type="button"
              onClick={() => {
                setTab(key);
                if (key === "drill") setDrillOpen(true);
              }}
              className={`flex-1 rounded-xl px-3 py-1.5 text-sm font-extrabold transition-all ${
                (key === "drill" && drillOpen) || (key !== "drill" && tab === key)
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-white hover:text-foreground"
              }`}
            >
              {icon} {t(labelKey)}
            </button>
          ))}
        </div>
      )}

      {/* Tab content */}
      {tab === "sentence" && card.id !== null && (
        <SentencePractice
          key={card.id}
          cardId={card.id}
          word={card.word}
          onFeedback={handleFeedback}
        />
      )}
      {tab === "pronounce" && (
        <PronounceControls
          key={card.id ?? "no-card"}
          word={card.word}
          cardId={card.id}
          onResult={handlePronounceResult}
        />
      )}
      {tab === "drill" && drillOpen && card.id !== null && (
        <DrillChat
          key={card.id}
          cardId={card.id}
          word={card.word}
          onClose={() => {
            setDrillOpen(false);
            setTab("sentence");
          }}
        />
      )}

      {/* Sentence feedback */}
      {tab === "sentence" && verdict !== "idle" && <PracticeFeedback verdict={verdict} />}
      {/* Pronunciation feedback */}
      {tab === "pronounce" && pronounceVerdict !== "idle" && (
        <PracticeFeedback verdict={pronounceVerdict} />
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button
          variant="outline"
          onClick={() => setIndex((i) => Math.max(0, i - 1))}
          disabled={index === 0}
          className="rounded-full"
        >
          {t("practice.back")}
        </Button>
        <Button
          variant="default"
          onClick={() => setIndex((i) => i + 1)}
          disabled={index >= snapshot.length - 1}
          className="rounded-full px-8"
        >
          {t("practice.continue")}
        </Button>
      </div>
    </div>
  );
}
