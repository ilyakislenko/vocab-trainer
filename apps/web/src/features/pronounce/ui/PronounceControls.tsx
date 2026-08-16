import { useMemo, useState } from "react";
import type { Feedback } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Loader } from "@/shared/ui/loader";
import { MicButton } from "@/shared/ui/mic-button";
import { SpeakButton } from "@/shared/ui/speak-button";
import { useCheckSentence } from "../model/use-check-sentence";
import { useExample } from "../model/use-example";

type Grammar =
  | { state: "idle" }
  | { state: "pending" }
  | { state: "checked"; feedback: Feedback }
  | { state: "error" };

function stripPunctuation(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z'\s-]/g, "")
    .split(/\s+/)
    .filter(Boolean);
}

function coverage(spoken: string, target: string): { covered: string[]; missed: string[] } {
  const spokenWords = new Set(stripPunctuation(spoken));
  const targetWords = stripPunctuation(target);
  const covered = targetWords.filter((w) => spokenWords.has(w));
  const missed = targetWords.filter((w) => !spokenWords.has(w));
  return { covered, missed };
}

function sentenceMatches(spoken: string, target: string): boolean {
  const { covered, missed } = coverage(spoken, target);
  const total = covered.length + missed.length;
  return total > 0 && covered.length / total >= 0.6;
}

export function PronounceControls({
  word,
  cardId,
  onResult,
}: {
  word: string;
  cardId?: number | null;
  onResult?: (matched: boolean) => void;
}) {
  const { t } = useI18n();
  const [heard, setHeard] = useState<string | null>(null);
  const [matched, setMatched] = useState(false);
  const [grammar, setGrammar] = useState<Grammar>({ state: "idle" });
  const [sentenceHeard, setSentenceHeard] = useState<string | null>(null);
  const [sentenceMatched, setSentenceMatched] = useState(false);
  const check = useCheckSentence(cardId ?? null);
  const example = useExample(cardId ?? null);
  const exampleText = example.data?.trim();

  const sentenceResult = useMemo(
    () => (sentenceHeard !== null && exampleText ? coverage(sentenceHeard, exampleText) : null),
    [sentenceHeard, exampleText],
  );

  const handleTranscript = async (transcript: string) => {
    const tokens = transcript.split(/\s+/);
    const isMatch = tokens.includes(word.trim().toLowerCase());
    setHeard(transcript);
    setMatched(isMatch);
    onResult?.(isMatch);
    if (isMatch && cardId != null && tokens.length > 1) {
      setGrammar({ state: "pending" });
      try {
        const feedback = await check.mutateAsync(transcript);
        setGrammar({ state: "checked", feedback });
      } catch {
        setGrammar({ state: "error" });
      }
    }
  };

  const handleTranscriptError = () => {
    setHeard("");
    setMatched(false);
    onResult?.(false);
    setGrammar({ state: "idle" });
  };

  const handleSentenceTranscript = (transcript: string) => {
    if (!exampleText) return;
    const ok = sentenceMatches(transcript, exampleText);
    setSentenceHeard(transcript);
    setSentenceMatched(ok);
    onResult?.(ok);
  };

  const handleSentenceError = () => {
    setSentenceHeard("");
    setSentenceMatched(false);
    onResult?.(false);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <SpeakButton text={word} label={t("practice.hear")} />
        <MicButton
          onTranscript={handleTranscript}
          onError={handleTranscriptError}
          label={t("practice.say")}
        />
      </div>

      {heard !== null &&
        (matched ? (
          <div className="flex flex-col gap-1 text-sm">
            {grammar.state === "pending" ? (
              <>
                <p>{t("pronounce.matched")}</p>
                <Loader label={t("pronounce.checkingGrammar")} />
              </>
            ) : grammar.state === "checked" && grammar.feedback.verdict === "needs_work" ? (
              <>
                <p>{t("pronounce.matched")}</p>
                <p className="text-amber-600">{grammar.feedback.feedback}</p>
                {grammar.feedback.corrected && (
                  <p>{t("pronounce.sayLike").replace("{text}", grammar.feedback.corrected)}</p>
                )}
                {grammar.feedback.example && (
                  <p>{t("pronounce.nativeWay").replace("{text}", grammar.feedback.example)}</p>
                )}
              </>
            ) : (
              <p>{t("pronounce.matched")}</p>
            )}
          </div>
        ) : (
          <p className="text-sm">
            {t("pronounce.notMatched").replace(
              "{heard}",
              heard?.trim() ? heard : t("pronounce.heardNothing"),
            )}
          </p>
        ))}

      {cardId != null && exampleText && (
        <div className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-3">
          <p className="text-sm">
            <span className="font-medium">{t("practice.exampleLabel")}</span> {exampleText}
          </p>
          <div className="flex gap-2">
            <SpeakButton text={exampleText} label={t("practice.hear")} />
            <MicButton
              onTranscript={handleSentenceTranscript}
              onError={handleSentenceError}
              label={t("practice.saySentence")}
            />
          </div>
          {example.isLoading && <Loader label={t("practice.hintLoading")} />}
          {sentenceHeard !== null && (
            <div className="flex flex-col gap-1 text-sm">
              {sentenceMatched ? (
                <p className="text-green-700">{t("pronounce.sentenceMatched")}</p>
              ) : (
                <>
                  <p className="text-red-600">{t("pronounce.sentenceNotMatched")}</p>
                  {sentenceResult && sentenceResult.missed.length > 0 && (
                    <p className="text-muted-foreground">
                      {t("pronounce.sentenceMissed")} {sentenceResult.missed.join(", ")}
                    </p>
                  )}
                  <p className="text-muted-foreground">
                    {t("pronounce.sentenceHeard")} "{sentenceHeard.trim()}"
                  </p>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
