import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { Loader } from "@/shared/ui/loader";
import { MicButton } from "@/shared/ui/mic-button";
import { Textarea } from "@/shared/ui/textarea";
import { useCheckSentence, useSuggestExample } from "../model/use-practice";

export function SentencePractice({
  cardId,
  word,
  onFeedback,
}: {
  cardId: number;
  word: string;
  onFeedback?: (verdict: "ok" | "needs_work") => void;
}) {
  const [sentence, setSentence] = useState("");
  const { t } = useI18n();
  const check = useCheckSentence(cardId);
  const example = useSuggestExample(cardId);
  const feedback = check.data;

  useEffect(() => {
    if (feedback?.verdict && onFeedback) onFeedback(feedback.verdict);
  }, [feedback, onFeedback]);

  useEffect(() => {
    if (check.isError) toast.error(t("feedback.unavailable"));
  }, [check.isError, t]);

  useEffect(() => {
    if (example.isError) toast.error(t("feedback.exampleError"));
  }, [example.isError, t]);

  const appendTranscript = (transcript: string) => {
    setSentence((prev) => (prev ? `${prev} ${transcript}` : transcript));
  };

  return (
    <div className="flex flex-col gap-3">
      <p>
        {t("practice.writeSentence")} <span className="font-semibold">{word}</span>:
      </p>
      <div className="flex gap-2">
        <Textarea
          aria-label={t("practice.yourSentence")}
          value={sentence}
          onChange={(e) => setSentence(e.target.value)}
          rows={3}
          className="flex-1"
        />
        <MicButton
          onTranscript={appendTranscript}
          onError={() => toast.error(t("practice.speechFailed"))}
          continuous
        />
      </div>
      <div className="flex gap-2">
        <Button
          onClick={() => check.mutate(sentence)}
          disabled={check.isPending || !sentence.trim()}
        >
          {t("practice.check")}
        </Button>
        <Button variant="secondary" onClick={() => example.mutate()} disabled={example.isPending}>
          {t("practice.getExample")}
        </Button>
      </div>
      {(check.isPending || example.isPending) && <Loader />}
      {feedback && (
        <div
          className={`rounded-lg border p-4 text-sm ${
            feedback.verdict === "ok"
              ? "border-green-200 bg-green-50"
              : "border-amber-200 bg-amber-50"
          }`}
        >
          <span
            className={`text-base font-semibold ${
              feedback.verdict === "ok" ? "text-green-700" : "text-amber-700"
            }`}
          >
            {feedback.verdict === "ok" ? t("feedback.ok") : t("feedback.needsWork")}
          </span>

          {feedback.verdict === "needs_work" && feedback.feedback && (
            <p className="mt-2 text-foreground">{feedback.feedback}</p>
          )}

          {feedback.corrected && feedback.verdict === "needs_work" && (
            <div className="mt-2 rounded-md bg-foreground/10 px-3 py-2">
              <span className="text-xs font-medium text-muted-foreground">
                {t("feedback.correctedLabel")}
              </span>
              <p className="mt-0.5 font-medium text-foreground">{feedback.corrected}</p>
            </div>
          )}

          {feedback.example && (
            <p className="mt-2 text-muted-foreground">
              <span className="text-xs font-medium">{t("practice.exampleLabel")}</span>{" "}
              {feedback.example}
            </p>
          )}
        </div>
      )}
      {/* Reserved slot for the suggested example so the layout does not jump */}
      <div className="flex min-h-10 items-start" aria-live="polite">
        {example.data && (
          <p className="text-muted-foreground text-sm">
            {t("practice.exampleLabel")} {example.data}
          </p>
        )}
      </div>
    </div>
  );
}
