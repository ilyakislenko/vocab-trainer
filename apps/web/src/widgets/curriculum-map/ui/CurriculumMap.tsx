import { Link } from "react-router-dom";
import { useCurriculumMap } from "@/entities/curriculum";
import type { CurriculumModule } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";

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

function ModuleStatusBadge({ module }: { module: CurriculumModule }) {
  const { t } = useI18n();
  if (module.availability !== "available") {
    return (
      <span className="rounded-full bg-muted px-3 py-1 text-xs font-extrabold text-muted-foreground">
        {t("learn.authoring")}
      </span>
    );
  }
  const labelKey =
    module.status === "completed"
      ? "learn.statusCompleted"
      : module.status === "in_progress"
        ? "learn.statusInProgress"
        : "learn.statusNotStarted";
  const tone =
    module.status === "completed"
      ? "bg-green-100 text-green-800"
      : module.status === "in_progress"
        ? "bg-tint-blue text-secondary-foreground"
        : "bg-muted text-muted-foreground";
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-extrabold ${tone}`}>{t(labelKey)}</span>
  );
}

function ModuleCard({ module }: { module: CurriculumModule }) {
  const { t } = useI18n();
  const content = (
    <>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-black leading-tight text-foreground">{module.title}</h3>
        {typeof module.quiz_best_score === "number" && (
          <span className="shrink-0 rounded-full bg-tint-lavender px-2 py-1 text-xs font-extrabold text-secondary-foreground">
            {Math.round(module.quiz_best_score)}%
          </span>
        )}
      </div>
      <div className="mt-3 flex items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
          {t(TRACK_LABEL_KEYS[module.track] ?? module.track)}
        </span>
        <ModuleStatusBadge module={module} />
      </div>
    </>
  );

  if (module.availability !== "available") {
    return <div className="rounded-3xl border border-border bg-card p-4 opacity-70">{content}</div>;
  }

  return (
    <Link
      to={`/learn/${module.id}`}
      className="block rounded-3xl border border-border bg-card p-4 transition-colors hover:border-primary hover:bg-tint-lavender/40"
    >
      {content}
    </Link>
  );
}

function LevelSection({ level, moduleList }: { level: string; moduleList: CurriculumModule[] }) {
  const { t } = useI18n();
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-black tracking-tight text-foreground">
        {t(LEVEL_LABEL_KEYS[level] ?? level)}
      </h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {moduleList.map((module) => (
          <ModuleCard key={module.id} module={module} />
        ))}
      </div>
    </section>
  );
}

export function CurriculumMap() {
  const { t } = useI18n();
  const map = useCurriculumMap();

  return (
    <div className="flex flex-col gap-8">
      <header className="flex items-end justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-black tracking-tight text-foreground">{t("learn.title")}</h1>
          <p className="text-sm font-medium text-muted-foreground">{t("learn.subtitle")}</p>
        </div>
        <Link
          to="/learn/skills"
          className="shrink-0 rounded-full border border-border px-4 py-2 text-sm font-extrabold text-muted-foreground hover:text-foreground"
        >
          {t("learn.skillReviews")}
        </Link>
      </header>

      {map.isLoading ? (
        <p className="text-sm font-semibold text-muted-foreground">{t("practice.loading")}</p>
      ) : map.error ? (
        <p className="rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-700">
          {t("misc.error")}
        </p>
      ) : (
        map.data?.levels.map((level) => (
          <LevelSection key={level.level} level={level.level} moduleList={level.modules} />
        ))
      )}
    </div>
  );
}
