import { useState } from "react";
import { useDeckCards, useReviewQueue, useTopicWords } from "@/entities/card";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";
import { PracticeSession } from "@/widgets/practice-session";

type Mode = "due" | "all" | "topic";

const MODES: { value: Mode; labelKey: string }[] = [
  { value: "due", labelKey: "practice.due" },
  { value: "all", labelKey: "practice.all" },
  { value: "topic", labelKey: "practice.topic" },
];

export function PracticePage({ deckId }: { deckId: number | null }) {
  const { t } = useI18n();
  const [mode, setMode] = useState<Mode>("due");
  const [section, setSection] = useState<string>("");
  const [topic, setTopic] = useState("");
  const [appliedTopic, setAppliedTopic] = useState<string | null>(null);

  const due = useReviewQueue(deckId, 20, mode === "due");
  const all = useDeckCards(deckId, mode === "all");
  const topicWords = useTopicWords(deckId, appliedTopic);

  if (deckId === null) return <p className="text-muted-foreground">{t("practice.noDeck")}</p>;

  const sections = [...new Set((all.data ?? []).map((c) => c.section).filter(Boolean))];
  const sectioned = section ? (all.data ?? []).filter((c) => c.section === section) : all.data;

  const cards = mode === "due" ? due.data : mode === "all" ? sectioned : topicWords.data;
  const isLoading =
    mode === "due" ? due.isLoading : mode === "all" ? all.isLoading : topicWords.isLoading;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex gap-1 rounded-2xl border border-border bg-card p-1">
          {MODES.map((m) => (
            <Button
              key={m.value}
              variant={mode === m.value ? "default" : "ghost"}
              onClick={() => setMode(m.value)}
              className={
                mode === m.value ? "rounded-xl font-extrabold" : "rounded-xl text-muted-foreground"
              }
            >
              {t(m.labelKey)}
            </Button>
          ))}
        </div>
        {mode === "all" && sections.length > 0 && (
          <Select value={section} onValueChange={(value) => setSection(value ?? "")}>
            <SelectTrigger className="w-44 rounded-full">
              <SelectValue>
                {(selected: string | null) =>
                  selected ? `${t("practice.section")}: ${selected}` : t("practice.allSections")
                }
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">{t("practice.allSections")}</SelectItem>
              {sections.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {mode === "topic" && (
        <div className="flex flex-col gap-2">
          <Textarea
            placeholder={t("practice.topicPlaceholder")}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
          <Button
            className="w-fit rounded-full px-6"
            onClick={() => setAppliedTopic(topic.trim() || null)}
            disabled={!topic.trim()}
          >
            {t("practice.findWords")}
          </Button>
        </div>
      )}

      <PracticeSession
        key={`${mode}:${section}:${appliedTopic}`}
        cards={cards}
        isLoading={isLoading}
      />
    </div>
  );
}
