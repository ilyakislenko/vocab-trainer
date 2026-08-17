import { Link } from "react-router-dom";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";

export function NoDeck() {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl border border-border bg-card p-10 text-center">
      <p className="text-2xl font-black tracking-tight">{t("noDeck.title")}</p>
      <p className="max-w-sm text-muted-foreground">{t("noDeck.hint")}</p>
      <Link to="/import">
        <Button className="rounded-full px-6">{t("noDeck.import")}</Button>
      </Link>
    </div>
  );
}
