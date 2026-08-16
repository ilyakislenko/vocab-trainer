import { Tooltip } from "@base-ui/react/tooltip";
import { useTranslateSentence } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";

export function HoverableSentence({ text, children }: { text: string; children: React.ReactNode }) {
  const { t } = useI18n();
  const translation = useTranslateSentence(text);

  return (
    <Tooltip.Root>
      <Tooltip.Trigger render={<span className="relative inline cursor-help" />} delay={0}>
        {children}
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Positioner sideOffset={6} align="start">
          <Tooltip.Popup className="z-50 max-w-sm rounded-lg border bg-popover p-3 text-sm shadow-lg">
            {translation.isLoading && (
              <p className="text-muted-foreground">{t("misc.translation")}</p>
            )}
            {translation.isError && <p className="text-destructive">{t("misc.error")}</p>}
            {translation.data && (
              <div className="flex flex-col gap-2">
                <p className="font-medium">{translation.data.full}</p>
                <div className="flex flex-wrap gap-1">
                  {translation.data.words.map((w) => (
                    <span
                      key={w.word}
                      className="rounded bg-muted px-1.5 py-0.5 text-xs"
                      title={w.translation}
                    >
                      {w.word}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </Tooltip.Popup>
        </Tooltip.Positioner>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
