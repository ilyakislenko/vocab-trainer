import { useState } from "react";
import type { ImportFormat } from "@/shared/api";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { useImportWords } from "../model/use-import-words";

export function ImportForm({ deckId }: { deckId: number }) {
  const [raw, setRaw] = useState("");
  const [format, setFormat] = useState<ImportFormat>("csv");
  const importWords = useImportWords(deckId);
  const result = importWords.data;

  const run = (dryRun: boolean) => importWords.mutate({ raw, format, dryRun });

  return (
    <div className="flex flex-col gap-3">
      <Textarea
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        placeholder="word,transcription,translation"
        rows={8}
      />
      <div className="flex items-center gap-2">
        <select
          aria-label="format"
          value={format}
          onChange={(e) => setFormat(e.target.value as ImportFormat)}
        >
          <option value="csv">CSV</option>
          <option value="markdown">Markdown</option>
        </select>
        <Button variant="secondary" onClick={() => run(true)} disabled={importWords.isPending}>
          Preview
        </Button>
        <Button onClick={() => run(false)} disabled={importWords.isPending}>
          Import
        </Button>
      </div>
      {result && (
        <div className="text-sm">
          <p>
            {result.committed
              ? `Imported ${result.imported.length}`
              : `Preview: ${result.imported.length} word(s)`}
          </p>
          {result.errors.length > 0 && (
            <ul className="text-destructive">
              {result.errors.map((e) => (
                <li key={e.line}>
                  line {e.line}: {e.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
