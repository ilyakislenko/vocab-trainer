import Markdown from "react-markdown";
import { useNavigate } from "react-router-dom";
import remarkGfm from "remark-gfm";
import { useLesson, useMarkLessonRead } from "@/entities/curriculum";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";

const LEVEL_LABEL_KEYS: Record<string, string> = {
  A1: "learn.levelA1",
  A2: "learn.levelA2",
  B1: "learn.levelB1",
  B2: "learn.levelB2",
  C1: "learn.levelC1",
  C2: "learn.levelC2",
};

const TRACK_LABEL_KEYS: Record<string, string> = {
  grammar: "learn.trackGrammar",
  vocabulary: "learn.trackVocabulary",
  phrasal_verbs: "learn.trackPhrasalVerbs",
  collocations: "learn.trackCollocations",
  idioms: "learn.trackIdioms",
  business: "learn.trackBusiness",
};

export function LessonReader({ moduleId }: { moduleId: string }) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const lesson = useLesson(moduleId);
  const markRead = useMarkLessonRead();

  if (lesson.isLoading) {
    return <p className="text-sm font-semibold text-muted-foreground">{t("practice.loading")}</p>;
  }
  if (lesson.error || !lesson.data) {
    return (
      <p className="rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700">
        {t("misc.error")}
      </p>
    );
  }

  const { markdown, meta } = lesson.data;

  const handleMarkRead = async () => {
    await markRead.mutateAsync(moduleId);
    navigate("/learn");
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 rounded-3xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-center gap-2 text-xs font-extrabold">
          <span className="rounded-full bg-tint-lavender px-3 py-1 text-secondary-foreground">
            {t(LEVEL_LABEL_KEYS[meta.level] ?? meta.level)}
          </span>
          <span className="rounded-full bg-tint-blue px-3 py-1 text-secondary-foreground">
            {t(TRACK_LABEL_KEYS[meta.track] ?? meta.track)}
          </span>
          <span className="rounded-full bg-muted px-3 py-1 text-muted-foreground">
            {t("learn.estMinutes").replace("{n}", String(meta.estimated_minutes))}
          </span>
        </div>
        <h1 className="text-2xl font-black tracking-tight text-foreground">{meta.title}</h1>
        <Button
          onClick={handleMarkRead}
          disabled={markRead.isPending}
          className="w-fit rounded-full"
        >
          {markRead.isPending ? t("practice.loading") : t("learn.markRead")}
        </Button>
      </header>

      <article className="rounded-3xl border border-border bg-card p-6 sm:p-8">
        <div className="lesson-markdown">
          <Markdown remarkPlugins={[remarkGfm]}>{markdown}</Markdown>
        </div>
      </article>

      {meta.objectives.length > 0 && (
        <section className="rounded-3xl border border-border bg-card p-6">
          <h2 className="mb-3 text-sm font-black uppercase tracking-wider text-primary">
            {t("learn.objectives")}
          </h2>
          <ul className="flex flex-col gap-2 text-sm text-foreground">
            {meta.objectives.map((objective) => (
              <li key={objective} className="flex items-start gap-2">
                <span aria-hidden className="mt-0.5 text-primary">
                  ✓
                </span>
                <span>{objective}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {meta.skills.length > 0 && (
        <section className="rounded-3xl border border-border bg-card p-6">
          <h2 className="mb-3 text-sm font-black uppercase tracking-wider text-primary">
            {t("learn.skills")}
          </h2>
          <div className="flex flex-wrap gap-2">
            {meta.skills.map((skill) => (
              <span
                key={skill}
                className="rounded-full bg-muted px-3 py-1 text-xs font-extrabold text-muted-foreground"
              >
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}

      {meta.references.length > 0 && (
        <section className="rounded-3xl border border-border bg-card p-6">
          <h2 className="mb-3 text-sm font-black uppercase tracking-wider text-primary">
            {t("learn.references")}
          </h2>
          <ul className="flex flex-col gap-2 text-sm text-foreground">
            {meta.references.map((ref) => (
              <li key={`${ref.book}:${ref.locator}`}>
                <span className="font-bold">{ref.book}</span> — {ref.locator}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
