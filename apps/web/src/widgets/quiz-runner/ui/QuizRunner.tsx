import { type FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuiz } from "@/entities/quiz";
import { useTakeQuiz } from "@/features/take-quiz";
import type { CurriculumQuizGrade, CurriculumQuizItem } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";

type Answers = Record<string, string>;

export function QuizRunner({ moduleId }: { moduleId: string }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const quiz = useQuiz(moduleId);
  const grade = useTakeQuiz(moduleId);
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult] = useState<CurriculumQuizGrade | null>(null);

  if (quiz.isLoading) {
    return <p className="text-sm font-semibold text-muted-foreground">{t("common.loading")}</p>;
  }
  if (quiz.error || !quiz.data) {
    return (
      <p className="rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700">
        {t("misc.error")}
      </p>
    );
  }

  const setAnswer = (itemId: string, value: string) =>
    setAnswers((prev) => ({ ...prev, [itemId]: value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const payload = quiz.data.items
      .filter((item) => answers[item.id] !== undefined && answers[item.id] !== "")
      .map((item) => ({ item_id: item.id, given: answers[item.id] }));
    const outcome = await grade.mutateAsync(payload);
    setResult(outcome);
  };

  if (result) {
    return <QuizResults result={result} onBack={() => navigate("/learn")} />;
  }

  const answerCount = quiz.data.items.filter(
    (item) => answers[item.id] !== undefined && answers[item.id] !== "",
  ).length;

  return (
    <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
      <header className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-black tracking-tight text-foreground">{t("quiz.title")}</h1>
          <span className="rounded-full bg-muted px-3 py-1 text-xs font-extrabold text-muted-foreground">
            {t("quiz.answered")
              .replace("{n}", String(answerCount))
              .replace("{total}", String(quiz.data.items.length))}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{t("quiz.hint")}</p>
      </header>

      <ol className="flex flex-col gap-4">
        {quiz.data.items.map((item, index) => (
          <li key={item.id}>
            <QuizItemCard
              item={item}
              number={index + 1}
              value={answers[item.id] ?? ""}
              onSelect={setAnswer}
            />
          </li>
        ))}
      </ol>

      <Button
        type="submit"
        disabled={grade.isPending || answerCount === 0}
        className="w-fit rounded-full"
      >
        {grade.isPending ? t("common.loading") : t("quiz.submit")}
      </Button>
    </form>
  );
}

function QuizItemCard({
  item,
  number,
  value,
  onSelect,
}: {
  item: CurriculumQuizItem;
  number: number;
  value: string;
  onSelect: (itemId: string, value: string) => void;
}) {
  const { t } = useI18n();
  if (item.type === "mcq" && item.options) {
    return <McqItem item={item} number={number} value={value} onSelect={onSelect} />;
  }
  return (
    <div className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
      <ItemHeader item={item} number={number} />
      <label
        htmlFor={`quiz-input-${item.id}`}
        className="flex flex-col gap-2 text-sm font-black uppercase tracking-wider text-muted-foreground"
      >
        {t(`quiz.type.${item.type}`)}
      </label>
      {item.type === "cloze" ? (
        <input
          id={`quiz-input-${item.id}`}
          value={value}
          onChange={(e) => onSelect(item.id, e.target.value)}
          className="rounded-2xl border border-border bg-background px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          autoComplete="off"
        />
      ) : (
        <textarea
          id={`quiz-input-${item.id}`}
          value={value}
          onChange={(e) => onSelect(item.id, e.target.value)}
          rows={3}
          className="rounded-2xl border border-border bg-background px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      )}
    </div>
  );
}

function McqItem({
  item,
  number,
  value,
  onSelect,
}: {
  item: CurriculumQuizItem;
  number: number;
  value: string;
  onSelect: (itemId: string, value: string) => void;
}) {
  const { t } = useI18n();
  const groupRef = useRef<HTMLDivElement>(null);
  const options = item.options ?? [];

  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      const target = e.target;
      if (!(target instanceof HTMLElement)) return;
      if (target.closest("[data-quiz-mcq]") !== groupRef.current) return;
      const index = Number(e.key) - 1;
      if (e.key >= "1" && e.key <= "9" && index >= 0 && index < options.length) {
        e.preventDefault();
        onSelect(item.id, String(index));
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onSelect, item.id, options.length]);

  return (
    <div className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
      <ItemHeader item={item} number={number} />
      <p className="text-sm font-black uppercase tracking-wider text-muted-foreground">
        {t("quiz.type.mcq")}
      </p>
      <div ref={groupRef} data-quiz-mcq className="flex flex-col gap-2">
        {options.map((option, index) => {
          const selected = value === String(index);
          return (
            <button
              key={option}
              type="button"
              aria-pressed={selected}
              onClick={() => onSelect(item.id, String(index))}
              className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-left text-sm transition-colors ${
                selected
                  ? "border-primary bg-tint-lavender text-secondary-foreground"
                  : "border-border bg-background text-foreground hover:bg-muted"
              }`}
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-black text-muted-foreground">
                {index + 1}
              </span>
              <span>{option}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ItemHeader({ item, number }: { item: CurriculumQuizItem; number: number }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-2">
      <span className="rounded-full bg-tint-blue px-3 py-1 text-xs font-extrabold text-secondary-foreground">
        {t("quiz.question").replace("{n}", String(number))}
      </span>
      <p className="text-sm font-semibold text-foreground">{item.prompt}</p>
    </div>
  );
}

function QuizResults({ result, onBack }: { result: CurriculumQuizGrade; onBack: () => void }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const score = Math.round(result.score);
  const correct = result.items.filter((item) => item.correct).length;
  const nextHref = result.next_module_id ? `/learn/${result.next_module_id}/quiz` : "/learn";
  const nextLabel = result.next_module_id ? t("quiz.nextModule") : t("quiz.backToMap");

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
        <h1 className="text-2xl font-black tracking-tight text-foreground">
          {t("quiz.resultTitle")}
        </h1>
        <div className="flex flex-wrap items-center gap-2 text-sm font-extrabold">
          <span className="rounded-full bg-tint-lavender px-3 py-1 text-secondary-foreground">
            {t("quiz.score").replace("{score}", String(score))}
          </span>
          <span className="rounded-full bg-muted px-3 py-1 text-muted-foreground">
            {t("quiz.correct")
              .replace("{n}", String(correct))
              .replace("{total}", String(result.items.length))}
          </span>
          {result.completed && (
            <span className="rounded-full bg-tint-peach px-3 py-1 text-secondary-foreground">
              {t("quiz.completed")}
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={onBack} variant="outline" className="rounded-full">
            {t("quiz.backToMap")}
          </Button>
          <Button onClick={() => navigate(nextHref)} className="rounded-full">
            {nextLabel}
          </Button>
        </div>
      </header>

      <ol className="flex flex-col gap-4">
        {result.items.map((item, index) => (
          <li
            key={item.item_id}
            className="flex flex-col gap-2 rounded-3xl border border-border bg-card p-6"
          >
            <div className="flex items-center gap-2 text-sm font-black">
              <span aria-hidden className={item.correct ? "text-primary" : "text-red-500"}>
                {item.correct ? "✓" : "✗"}
              </span>
              <span className="text-foreground">
                {t("quiz.question").replace("{n}", String(index + 1))}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              <span className="font-bold text-foreground">
                {item.correct ? t("quiz.right") : t("quiz.wrong")}
              </span>{" "}
              {item.explanation}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}
