import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { usePlacement } from "@/entities/placement";
import { useTakePlacement } from "@/features/take-placement";
import type { PlacementGrade, PlacementItem } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { CardContent, Card as UICard } from "@/shared/ui/card";

type Answers = Record<string, string>;

export function PlacementRunner() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const placement = usePlacement();
  const grade = useTakePlacement();
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult] = useState<PlacementGrade | null>(null);

  if (placement.isLoading) {
    return <p className="text-sm font-semibold text-muted-foreground">{t("practice.loading")}</p>;
  }
  if (placement.error || !placement.data) {
    return (
      <p className="rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700">
        {t("misc.error")}
      </p>
    );
  }

  const items = placement.data.items;
  const item = items[index];

  const setAnswer = (itemId: string, value: string) =>
    setAnswers((prev) => ({ ...prev, [itemId]: value }));

  const goNext = () => {
    if (index + 1 < items.length) {
      setIndex((i) => i + 1);
    }
  };

  const goBack = () => {
    if (index > 0) setIndex((i) => i - 1);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const payload = items
      .filter((it) => answers[it.id] !== undefined && answers[it.id] !== "")
      .map((it) => ({ item_id: it.id, given: answers[it.id] }));
    const outcome = await grade.mutateAsync(payload);
    setResult(outcome);
  };

  if (result) {
    return <PlacementResult result={result} onContinue={navigate} />;
  }

  if (!item) {
    return null;
  }

  const answered = answers[item.id] !== undefined && answers[item.id] !== "";
  const isLast = index + 1 === items.length;
  const answeredCount = items.filter(
    (it) => answers[it.id] !== undefined && answers[it.id] !== "",
  ).length;

  return (
    <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
      <header className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            {t("placement.title")}
          </h1>
          <span className="rounded-full bg-muted px-3 py-1 text-xs font-extrabold text-muted-foreground">
            {t("quiz.answered")
              .replace("{n}", String(answeredCount))
              .replace("{total}", String(items.length))}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{t("placement.hint")}</p>
      </header>

      <UICard className="border-border bg-tint-lavender">
        <CardContent className="flex flex-col gap-4 py-10 text-center">
          <span className="rounded-full bg-background px-3 py-1 text-xs font-extrabold text-primary">
            {t("placement.level").replace("{level}", item.level)}
          </span>
          <p className="text-2xl font-black leading-snug tracking-tight text-foreground">
            {item.prompt}
          </p>
          <PlacementItemInput item={item} value={answers[item.id] ?? ""} onAnswer={setAnswer} />
        </CardContent>
      </UICard>

      <div className="flex items-center justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={goBack}
          disabled={index === 0}
          className="rounded-full"
        >
          {t("placement.back")}
        </Button>
        {isLast ? (
          <Button
            type="submit"
            disabled={grade.isPending || answeredCount === 0}
            className="rounded-full"
          >
            {grade.isPending ? t("practice.loading") : t("placement.submit")}
          </Button>
        ) : (
          <Button type="button" onClick={goNext} disabled={!answered} className="rounded-full">
            {t("placement.next")}
          </Button>
        )}
      </div>
    </form>
  );
}

function PlacementItemInput({
  item,
  value,
  onAnswer,
}: {
  item: PlacementItem;
  value: string;
  onAnswer: (itemId: string, value: string) => void;
}) {
  const { t } = useI18n();
  if (item.type === "mcq" && item.options) {
    return (
      <div className="flex flex-col gap-2">
        {item.options.map((option, optionIndex) => {
          const selected = value === String(optionIndex);
          return (
            <button
              key={option}
              type="button"
              aria-pressed={selected}
              onClick={() => onAnswer(item.id, String(optionIndex))}
              className={`flex items-center gap-3 rounded-2xl border bg-card px-4 py-3 text-left text-sm transition-colors ${
                selected
                  ? "border-primary bg-tint-lavender text-secondary-foreground"
                  : "border-border text-foreground hover:bg-muted"
              }`}
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-black text-muted-foreground">
                {optionIndex + 1}
              </span>
              <span>{option}</span>
            </button>
          );
        })}
      </div>
    );
  }
  return (
    <input
      id={`placement-input-${item.id}`}
      value={value}
      onChange={(e) => onAnswer(item.id, e.target.value)}
      placeholder={t(`placement.type.${item.type}`)}
      autoComplete="off"
      className="rounded-2xl border border-border bg-card px-4 py-3 text-center text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
    />
  );
}

function PlacementResult({
  result,
  onContinue,
}: {
  result: PlacementGrade;
  onContinue: (to: string) => void;
}) {
  const { t } = useI18n();
  const target = result.current_module_id ? `/learn/${result.current_module_id}` : "/learn";
  const correctCount = result.results.filter((r) => r.correct).length;
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-6 rounded-3xl border border-border bg-card p-8 text-center">
        <span className="text-5xl">🎯</span>
        <p className="text-2xl font-black tracking-tight">{t("placement.doneTitle")}</p>
        <div className="flex flex-col items-center gap-2">
          <span className="text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
            {t("placement.yourLevel")}
          </span>
          <span className="rounded-full bg-tint-lavender px-6 py-2 text-3xl font-black text-secondary-foreground">
            {result.level}
          </span>
        </div>
        <p className="max-w-sm text-sm text-muted-foreground">{t("placement.doneHint")}</p>
        <p className="text-sm font-semibold text-muted-foreground">
          {t("placement.reviewScore")
            .replace("{ok}", String(correctCount))
            .replace("{total}", String(result.results.length))}
        </p>
      </div>

      <div className="flex flex-col gap-2 rounded-3xl border border-border bg-card p-4">
        <h2 className="px-2 text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
          {t("placement.reviewTitle")}
        </h2>
        <ol className="flex max-h-80 flex-col gap-2 overflow-y-auto pr-1">
          {result.results.map((r) => (
            <li
              key={r.item_id}
              className="flex flex-col gap-1 rounded-2xl border bg-card p-3 text-left"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-bold text-foreground">{r.prompt}</p>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-extrabold ${
                    r.correct ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                  }`}
                >
                  {r.correct ? t("placement.reviewOk") : t("placement.reviewMiss")}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {t("placement.reviewYourAnswer").replace("{given}", r.given || "—")}
              </p>
              <p className="text-xs font-semibold text-emerald-700">
                {t("placement.reviewCorrectAnswer").replace("{answer}", r.correct_answer)}
              </p>
              {!r.correct && <p className="text-xs text-muted-foreground">{r.explanation}</p>}
            </li>
          ))}
        </ol>
      </div>

      <Button onClick={() => onContinue(target)} className="rounded-full px-8">
        {t("placement.startLearning")}
      </Button>
    </div>
  );
}
