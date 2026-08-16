import { useRef, useState } from "react";
import type { ImportFormat } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";
import { useImportWords } from "../model/use-import-words";

function detectFormat(filename: string): ImportFormat {
  if (filename.endsWith(".md")) return "markdown";
  return "csv";
}

export function ImportForm({ deckId }: { deckId: number }) {
  const { t } = useI18n();
  const [raw, setRaw] = useState("");
  const [format, setFormat] = useState<ImportFormat>("csv");
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const importWords = useImportWords(deckId);
  const result = importWords.data;

  const run = (dryRun: boolean) => importWords.mutate({ raw, format, dryRun });

  const handleFile = (file: File) => {
    setFormat(detectFormat(file.name));
    file.text().then(setRaw);
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Drop zone */}
      <button
        type="button"
        className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${
          dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/30"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        }}
        onClick={() => fileRef.current?.click()}
      >
        <span className="text-4xl">📁</span>
        <p className="mt-3 text-sm font-medium text-muted-foreground">
          {dragOver ? t("import.dropFile") : t("import.browse")}
        </p>
        <input
          ref={fileRef}
          type="file"
          accept=".csv,.md,.txt"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
      </button>

      <Textarea
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        placeholder={t("import.placeholder")}
        rows={8}
      />
      <div className="flex items-center gap-2">
        <select
          aria-label={t("import.formatLabel")}
          value={format}
          onChange={(e) => setFormat(e.target.value as ImportFormat)}
        >
          <option value="csv">{t("import.csv")}</option>
          <option value="markdown">{t("import.markdown")}</option>
        </select>
        <Button variant="secondary" onClick={() => run(true)} disabled={importWords.isPending}>
          {t("import.dryRun")}
        </Button>
        <Button onClick={() => run(false)} disabled={importWords.isPending}>
          {t("import.commit")}
        </Button>
      </div>
      {importWords.isError && <p role="alert">{t("feedback.unavailable")}</p>}
      {result && (
        <div className="text-sm">
          <p>
            {result.committed
              ? t("import.imported").replace("{count}", String(result.imported.length))
              : t("import.preview").replace("{count}", String(result.imported.length))}
          </p>
          {result.errors.length > 0 && (
            <ul className="text-destructive">
              {result.errors.map((e) => (
                <li key={e.line}>
                  {t("import.lineError")
                    .replace("{line}", String(e.line))
                    .replace("{reason}", e.reason)}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
