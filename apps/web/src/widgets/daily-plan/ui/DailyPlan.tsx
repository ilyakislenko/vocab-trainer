import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTodaySession } from "@/entities/session";
import type { TodayStep } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";

function StepCard({ children }: { children: ReactNode }) {
  return (
    <li className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-5">{children}</li>
  );
}

function ReviewCard({ step }: { step: TodayStep }) {
  const { t } = useI18n();
  return (
    <StepCard>
      <h3 className="text-lg font-black tracking-tight text-foreground">
        {t("today.review.title")}
      </h3>
      <div className="flex flex-wrap gap-2 text-sm font-extrabold text-muted-foreground">
        {step.vocab_due > 0 && (
          <Link to="/" className="rounded-full bg-primary/10 px-3 py-1 text-primary">
            {t("today.review.vocab")} · {step.vocab_due}
          </Link>
        )}
        {step.skill_due > 0 && (
          <Link to="/learn/skills" className="rounded-full bg-primary/10 px-3 py-1 text-primary">
            {t("today.review.skills")} · {step.skill_due}
          </Link>
        )}
      </div>
    </StepCard>
  );
}

function LearnCard({ step }: { step: TodayStep }) {
  const { t } = useI18n();
  const isLesson = step.kind === "read_lesson";
  const to = isLesson ? `/learn/${step.module_id}` : `/learn/${step.module_id}/quiz`;
  return (
    <StepCard>
      <h3 className="text-lg font-black tracking-tight text-foreground">
        {isLesson ? t("today.learn.readLesson") : t("today.learn.takeQuiz")}
      </h3>
      <Link to={to} className="text-base font-extrabold text-primary">
        {step.title} · {step.level} {step.track}
      </Link>
      {step.items !== null && step.items !== undefined && step.items > 0 && (
        <p className="text-sm font-extrabold text-muted-foreground">
          {t("today.learn.items")} · {step.items}
        </p>
      )}
    </StepCard>
  );
}

function ProduceCard({ step }: { step: TodayStep }) {
  const { t } = useI18n();
  const sections = step.vocab_sections ?? [];
  const interviewTopic = step.interview_topic ?? null;
  return (
    <StepCard>
      <h3 className="text-lg font-black tracking-tight text-foreground">
        {t("today.produce.title")}
      </h3>
      {sections.length > 0 ? (
        <>
          <p className="text-sm font-bold text-muted-foreground">
            {t("today.produce.vocabPrompt")}
          </p>
          <div className="flex flex-wrap gap-2">
            {sections.map((name) => (
              <Link
                key={name}
                to={`/practice?section=${encodeURIComponent(name)}`}
                className="rounded-full bg-primary/10 px-3 py-1 text-sm font-extrabold text-primary"
              >
                {t("today.produce.section")}: {name}
              </Link>
            ))}
          </div>
        </>
      ) : interviewTopic ? (
        <>
          <p className="text-sm font-bold text-muted-foreground">
            {t("today.produce.interviewPrompt")}
          </p>
          <Link
            to={`/interview?topic=${encodeURIComponent(interviewTopic)}`}
            className="text-base font-extrabold text-primary"
          >
            {interviewTopic}
          </Link>
        </>
      ) : (
        <>
          <p className="text-sm font-bold text-muted-foreground">
            {t("today.produce.prompt")}: &quot;{step.word}&quot;
          </p>
          <Link to="/practice" className="text-base font-extrabold text-primary">
            {t("today.produce.go")}
          </Link>
        </>
      )}
    </StepCard>
  );
}

function FocusCard({ step }: { step: TodayStep }) {
  const { t } = useI18n();
  const leeches = step.leeches ?? [];
  if (leeches.length === 0) return null;
  return (
    <StepCard>
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-black tracking-tight text-foreground">
          {t("today.focus.title")}
        </h3>
        <span className="rounded-full bg-destructive/10 px-3 py-1 text-sm font-extrabold text-destructive">
          {leeches.length} {t("today.focus.leeches")}
        </span>
      </div>
      <ul className="flex flex-wrap gap-2">
        {leeches.map((item) => (
          <li
            key={item.id}
            className="rounded-full bg-white px-3 py-1 text-sm font-extrabold text-destructive"
          >
            {item.skill}
          </li>
        ))}
      </ul>
      <Link to="/learn/skills" className="text-base font-extrabold text-primary">
        {t("today.focus.go")}
      </Link>
    </StepCard>
  );
}

export function DailyPlan() {
  const { t } = useI18n();
  const session = useTodaySession();

  if (session.isLoading) {
    return <p className="text-sm font-bold text-muted-foreground">{t("today.loading")}</p>;
  }
  if (session.isError || !session.data) {
    return <p className="text-sm font-bold text-destructive">{t("today.error")}</p>;
  }

  const steps = session.data.steps;
  if (steps.length === 0) {
    return <p className="text-sm font-bold text-muted-foreground">{t("today.empty")}</p>;
  }

  return (
    <ol className="flex flex-col gap-4">
      {steps.map((step) => {
        if (step.kind === "review") return <ReviewCard key={step.kind} step={step} />;
        if (step.kind === "read_lesson" || step.kind === "take_quiz")
          return <LearnCard key={step.kind} step={step} />;
        if (step.kind === "produce") return <ProduceCard key={step.kind} step={step} />;
        return <FocusCard key={step.kind} step={step} />;
      })}
    </ol>
  );
}
