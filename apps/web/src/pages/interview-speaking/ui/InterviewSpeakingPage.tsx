import { useI18n } from "@/shared/lib/i18n";
import { PhrasePractice } from "@/widgets/phrase-practice";

export function InterviewSpeakingPage() {
  const { t } = useI18n();
  return (
    <div className="flex max-w-2xl flex-col gap-4">
      <p className="text-xs font-black uppercase tracking-widest text-primary">
        {t("speaking.title")}
      </p>
      <h2 className="text-2xl font-black tracking-tight">{t("speaking.subtitle")}</h2>
      <PhrasePractice />
    </div>
  );
}
