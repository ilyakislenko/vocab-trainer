import { useState } from "react";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { useCheckSentence, useSuggestExample } from "../model/use-practice";

export function SentencePractice({ cardId, word }: { cardId: number; word: string }) {
  const [sentence, setSentence] = useState("");
  const check = useCheckSentence(cardId);
  const example = useSuggestExample(cardId);
  const feedback = check.data;

  return (
    <div className="flex flex-col gap-3">
      <p>
        Write a sentence using <span className="font-semibold">{word}</span>:
      </p>
      <Textarea value={sentence} onChange={(e) => setSentence(e.target.value)} rows={3} />
      <div className="flex gap-2">
        <Button
          onClick={() => check.mutate(sentence)}
          disabled={check.isPending || !sentence.trim()}
        >
          Check
        </Button>
        <Button variant="secondary" onClick={() => example.mutate()} disabled={example.isPending}>
          Get an example
        </Button>
      </div>
      {check.isError && (
        <p role="alert" className="text-destructive">
          The language model is unavailable.
        </p>
      )}
      {feedback && (
        <div className="rounded-md border p-3 text-sm">
          <span className={feedback.verdict === "ok" ? "text-green-600" : "text-amber-600"}>
            {feedback.verdict === "ok" ? "Looks good" : "Needs work"}
          </span>
          <p>{feedback.feedback}</p>
          {feedback.corrected && <p>Corrected: {feedback.corrected}</p>}
          {feedback.example && <p className="text-muted-foreground">e.g. {feedback.example}</p>}
        </div>
      )}
      {example.data && <p className="text-muted-foreground text-sm">Example: {example.data}</p>}
    </div>
  );
}
