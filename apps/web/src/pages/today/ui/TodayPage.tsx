import { useI18n } from "@/shared/lib/i18n";
import { DailyPlan } from "@/widgets/daily-plan";

export function TodayPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <header>
        <h2 className="text-2xl font-black tracking-tight text-foreground">
          {t("today.pageTitle")}
        </h2>
        <p className="mt-1 text-sm font-bold text-muted-foreground">{t("today.pageHint")}</p>
      </header>
      <DailyPlan />
    </div>
  );
}
