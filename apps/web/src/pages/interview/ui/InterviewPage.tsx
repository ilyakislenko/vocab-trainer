import { useState } from "react";
import { InterviewChat } from "@/features/interview";
import { useI18n } from "@/shared/lib/i18n";

export function InterviewPage() {
  const { t } = useI18n();
  const [topic, setTopic] = useState<string | null>(null);

  return (
    <div className="flex max-w-2xl flex-col gap-4">
      <p className="text-xs font-black uppercase tracking-widest text-primary">
        {t("interview.title")}
      </p>
      <h2 className="text-2xl font-black tracking-tight">{t("interview.subtitle")}</h2>
      <InterviewChat topic={topic} onTopicChange={setTopic} />
    </div>
  );
}
