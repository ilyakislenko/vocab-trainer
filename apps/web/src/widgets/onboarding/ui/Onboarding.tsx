import { BookOpen, Pencil, Upload } from "lucide-react";
import { useI18n } from "@/shared/lib/i18n";

const STEPS = [
  { icon: BookOpen, key: "onboarding.step1", tint: "bg-tint-lavender" },
  { icon: Upload, key: "onboarding.step2", tint: "bg-tint-blue" },
  { icon: Pencil, key: "onboarding.step3", tint: "bg-tint-peach" },
];

export function Onboarding() {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center gap-8 rounded-3xl border border-border bg-card p-12 text-center">
      <div className="flex flex-col gap-2">
        <p className="text-3xl font-black tracking-tight">{t("onboarding.welcome")}</p>
        <p className="max-w-md text-muted-foreground">{t("onboarding.firstRun")}</p>
      </div>
      <div className="flex gap-6">
        {STEPS.map(({ icon: Icon, key, tint }) => (
          <div
            key={key}
            className={`flex w-40 flex-col items-center gap-3 rounded-2xl border border-border p-6 ${tint}`}
          >
            <div className="flex size-14 items-center justify-center rounded-full bg-white">
              <Icon className="size-6 text-primary" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-extrabold">{t(key)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
