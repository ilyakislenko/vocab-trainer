import { useI18n } from "@/shared/lib/i18n";
import { PlacementRunner } from "@/widgets/placement-runner";

export function PlacementPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-black tracking-tight text-foreground">
          {t("placement.pageTitle")}
        </h1>
        <p className="text-sm text-muted-foreground">{t("placement.pageHint")}</p>
      </div>
      <PlacementRunner />
    </div>
  );
}
