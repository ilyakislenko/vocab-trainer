import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useSkillReviewQueue } from "@/entities/skill-item";
import { RatingBar } from "@/features/rate-card";
import { useRecordSkillReview } from "@/features/review-skills";
import type { CurriculumSkillReview, Rating } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { CardContent, Card as UICard } from "@/shared/ui/card";

export function SkillReviewSession() {
  const { t } = useI18n();
  const queue = useSkillReviewQueue();
  const record = useRecordSkillReview();
  const [session, setSession] = useState<CurriculumSkillReview[] | null>(null);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [reviewed, setReviewed] = useState(0);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    if (session === null && queue.data !== undefined) {
      setSession(queue.data);
      setComplete(queue.data.length === 0);
    }
  }, [queue.data, session]);

  if (session === null) return <p>{t("practice.loading")}</p>;
  const item = session[index];

  if (!item || complete) {
    return (
      <div className="flex flex-col items-center gap-6 rounded-3xl border border-border bg-card p-8 text-center">
        <span className="text-5xl">🎉</span>
        <p className="text-2xl font-black tracking-tight">
          {reviewed > 0 ? t("review.summary") : t("review.caughtUp")}
        </p>
        {reviewed > 0 && (
          <p className="text-muted-foreground">
            {t("skill.reviewed")}: {reviewed}
          </p>
        )}
        <Button
          onClick={() => {
            setSession(null);
            setIndex(0);
            setReviewed(0);
            setRevealed(false);
            setComplete(false);
          }}
          className="rounded-full"
        >
          {t("review.startAgain")}
        </Button>
      </div>
    );
  }

  const progress = session.length > 0 ? ((index + 1) / session.length) * 100 : 0;

  const rate = async (rating: Rating) => {
    try {
      await record.mutateAsync({ skillItemId: item.id, rating });
      setReviewed((n) => n + 1);
      setRevealed(false);
      setIndex((i) => i + 1);
      if (index + 1 >= session.length) setComplete(true);
    } catch {
      toast.error(t("feedback.unavailable"));
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex w-full max-w-md items-center gap-3">
        <div className="flex-1 overflow-hidden rounded-full bg-muted">
          <div
            className="h-2 rounded-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-sm text-muted-foreground tabular-nums">
          {index + 1} / {session.length}
        </span>
      </div>

      <UICard className="w-full max-w-md border-border bg-tint-lavender">
        <CardContent className="flex flex-col gap-4 py-10 text-center">
          <span className="rounded-full bg-white px-3 py-1 text-sm font-extrabold text-primary">
            {item.skill}
          </span>
          <p className="text-2xl font-black leading-snug tracking-tight text-foreground">
            {item.prompt}
          </p>
          {item.options && item.options.length > 0 && !revealed && (
            <div className="flex flex-wrap justify-center gap-2">
              {item.options.map((option) => (
                <span
                  key={option}
                  className="rounded-full bg-white px-3 py-1 text-sm font-bold text-foreground"
                >
                  {option}
                </span>
              ))}
            </div>
          )}
          {revealed && (
            <div className="flex flex-col items-center gap-2">
              <span className="text-sm font-extrabold uppercase tracking-widest text-muted-foreground">
                {t("skill.answers")}
              </span>
              <span className="text-2xl font-black text-primary">{item.answers.join(", ")}</span>
              <span className="mt-1 text-sm text-muted-foreground">
                {t("skill.explanation")}: {item.explanation}
              </span>
            </div>
          )}
        </CardContent>
      </UICard>

      {revealed ? (
        <RatingBar onRate={rate} disabled={record.isPending} />
      ) : (
        <Button onClick={() => setRevealed(true)} className="rounded-full px-8">
          {t("review.showAnswer")}
        </Button>
      )}
    </div>
  );
}
