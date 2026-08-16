import type { ComponentProps } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { speak } from "@/shared/lib/speech";
import { Button } from "@/shared/ui/button";

type SpeakVariant = Extract<
  ComponentProps<typeof Button>["variant"],
  "outline" | "ghost" | "secondary" | "default"
>;

export function SpeakButton({
  text,
  label,
  ariaLabel,
  className,
  variant = "outline",
  size,
}: {
  text: string;
  label?: string;
  ariaLabel?: string;
  className?: string;
  variant?: SpeakVariant;
  size?: ComponentProps<typeof Button>["size"];
}) {
  const { t } = useI18n();
  return (
    <Button
      variant={variant}
      size={size}
      onClick={() => speak(text)}
      className={className}
      aria-label={ariaLabel ?? t("practice.hearLabel")}
    >
      {label ?? "🔊"}
    </Button>
  );
}
