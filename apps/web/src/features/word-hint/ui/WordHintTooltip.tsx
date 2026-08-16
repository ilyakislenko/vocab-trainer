import type { ReactNode } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { useWordHint } from "../model/use-word-hint";

export function WordHintTooltip({ cardId, children }: { cardId: number; children: ReactNode }) {
  const { t } = useI18n();
  const hint = useWordHint(cardId);

  return (
    <span className="group/tooltip relative inline-flex cursor-help">
      {children}
      <span className="pointer-events-none absolute top-full left-1/2 z-50 mb-2 hidden w-72 -translate-x-1/2 rounded-xl border border-border bg-popover p-3 text-left text-sm shadow-lg group-hover/tooltip:block">
        {hint.isLoading && <p className="text-muted-foreground">{t("practice.hintLoading")}</p>}
        {hint.isError && <p className="text-muted-foreground">{t("practice.hintError")}</p>}
        {hint.data && (
          <div className="flex flex-col gap-2">
            <p className="text-foreground">{hint.data.meaning}</p>
            {hint.data.example && (
              <p className="text-muted-foreground">
                {t("misc.e.g.")} {hint.data.example}
              </p>
            )}
          </div>
        )}
      </span>
    </span>
  );
}
