import { Link } from "react-router-dom";
import { useCurriculumMap } from "@/entities/curriculum";
import { useI18n } from "@/shared/lib/i18n";
import { CurriculumMap } from "@/widgets/curriculum-map";
import { FocusList } from "@/widgets/focus-list";

export function LearnPage() {
  const { t } = useI18n();
  const map = useCurriculumMap();
  if (map.isLoading) return null;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between gap-4">
        <header>
          <h2 className="text-2xl font-black tracking-tight text-foreground">{t("learn.title")}</h2>
          <p className="mt-1 text-sm font-bold text-muted-foreground">{t("learn.subtitle")}</p>
        </header>
        <Link
          to="/today"
          className="rounded-full border border-border bg-card px-5 py-2 text-sm font-extrabold text-foreground transition-colors hover:bg-muted"
        >
          {t("nav.today")}
        </Link>
      </div>
      <CurriculumMap />
      <FocusList />
    </div>
  );
}
