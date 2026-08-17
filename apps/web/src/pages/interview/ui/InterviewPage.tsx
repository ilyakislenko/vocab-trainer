import { useSearchParams } from "react-router-dom";
import { INTERVIEW_TOPICS, InterviewChat } from "@/features/interview";
import { useI18n } from "@/shared/lib/i18n";

export function InterviewPage() {
  const { t } = useI18n();
  const [searchParams] = useSearchParams();
  const topic = searchParams.get("topic");
  const initialTopic =
    topic && INTERVIEW_TOPICS.some((candidate) => candidate === topic) ? topic : undefined;

  return (
    <div className="flex max-w-2xl flex-col gap-4">
      <p className="text-xs font-black uppercase tracking-widest text-primary">
        {t("interview.title")}
      </p>
      <h2 className="text-2xl font-black tracking-tight">{t("interview.subtitle")}</h2>
      <InterviewChat initialTopic={initialTopic} />
    </div>
  );
}
