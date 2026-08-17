import { Link } from "react-router-dom";
import { useI18n } from "@/shared/lib/i18n";
import { FocusList } from "@/widgets/focus-list";
import { SkillReviewSession } from "@/widgets/skill-review-session";

export function ReviewSkillsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-black tracking-tight text-foreground">{t("skill.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("skill.hint")}</p>
        </div>
        <Link
          to="/learn"
          className="shrink-0 rounded-full border border-border px-4 py-2 text-sm font-extrabold text-muted-foreground hover:text-foreground"
        >
          {t("learn.backToMap")}
        </Link>
      </div>
      <FocusList />
      <SkillReviewSession />
    </div>
  );
}
