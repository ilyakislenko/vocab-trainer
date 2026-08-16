import { useEffect } from "react";
import type { Rating } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";

const RATINGS: { rating: Rating; labelKey: string; classes: string }[] = [
  {
    rating: 1,
    labelKey: "review.ratingAgain",
    classes: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  },
  {
    rating: 2,
    labelKey: "review.ratingHard",
    classes: "bg-amber-500 text-white hover:bg-amber-500/90",
  },
  {
    rating: 3,
    labelKey: "review.ratingGood",
    classes: "bg-emerald-500 text-white hover:bg-emerald-500/90",
  },
  {
    rating: 4,
    labelKey: "review.ratingEasy",
    classes: "bg-primary text-primary-foreground hover:bg-primary/90",
  },
];

export function RatingBar({
  onRate,
  disabled,
}: {
  onRate: (rating: Rating) => void;
  disabled: boolean;
}) {
  const { t } = useI18n();
  useEffect(() => {
    if (disabled) return;
    const handler = (e: KeyboardEvent) => {
      const target = e.target;
      if (target instanceof HTMLElement) {
        const tag = target.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable) return;
      }
      const rating = Number(e.key);
      if (rating >= 1 && rating <= 4) onRate(rating as Rating);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onRate, disabled]);

  return (
    <div className="flex flex-wrap justify-center gap-2">
      {RATINGS.map(({ rating, labelKey, classes }) => (
        <Button
          key={rating}
          disabled={disabled}
          onClick={() => onRate(rating)}
          className={`${classes}`}
        >
          {t(labelKey)} <span className="ml-1 opacity-70">{rating}</span>
        </Button>
      ))}
    </div>
  );
}
