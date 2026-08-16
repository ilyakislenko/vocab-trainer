import { CheckCircle2, Lightbulb, TriangleAlert } from "lucide-react";
import { useI18n } from "@/shared/lib/i18n";

export function FeedbackCard({
  verdict,
  feedback,
  corrected,
}: {
  verdict: "ok" | "needs_work" | null;
  feedback: string;
  corrected?: string | null;
}) {
  const { t } = useI18n();

  const tone =
    verdict === "ok"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
      : verdict === "needs_work"
        ? "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300"
        : "border-border bg-muted/40 text-foreground";

  const icon =
    verdict === "ok" ? (
      <CheckCircle2 className="size-4 shrink-0" />
    ) : verdict === "needs_work" ? (
      <TriangleAlert className="size-4 shrink-0" />
    ) : (
      <Lightbulb className="size-4 shrink-0" />
    );

  const title =
    verdict === "ok"
      ? t("interview.good")
      : verdict === "needs_work"
        ? t("interview.needsWork")
        : null;

  return (
    <div className={`mr-auto max-w-[85%] rounded-xl border px-3 py-2 text-sm ${tone}`}>
      <div className="flex items-center gap-1.5 font-bold">
        {icon}
        {title && <span>{title}</span>}
      </div>
      <p className="mt-1 whitespace-pre-line leading-relaxed">{feedback}</p>
      {corrected && (
        <p className="mt-1.5 flex gap-1.5">
          <span className="font-bold">{t("interview.corrected")}</span>
          <span>{corrected}</span>
        </p>
      )}
    </div>
  );
}
