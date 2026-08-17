import { Link, useParams } from "react-router-dom";
import { useI18n } from "@/shared/lib/i18n";
import { QuizRunner } from "@/widgets/quiz-runner";

export function QuizPage() {
  const { moduleId } = useParams<{ moduleId: string }>();
  const { t } = useI18n();
  if (!moduleId) return null;
  return (
    <div className="flex flex-col gap-4">
      <Link
        to={`/learn/${moduleId}`}
        className="text-sm font-bold text-muted-foreground hover:text-foreground"
      >
        {t("learn.backToLesson")}
      </Link>
      <QuizRunner moduleId={moduleId} />
    </div>
  );
}
