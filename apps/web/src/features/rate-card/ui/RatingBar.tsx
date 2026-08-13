import { useEffect } from "react";
import type { Rating } from "@/shared/api";
import { Button } from "@/shared/ui/button";

const RATINGS: { rating: Rating; label: string }[] = [
  { rating: 1, label: "Again" },
  { rating: 2, label: "Hard" },
  { rating: 3, label: "Good" },
  { rating: 4, label: "Easy" },
];

export function RatingBar({
  onRate,
  disabled,
}: {
  onRate: (rating: Rating) => void;
  disabled: boolean;
}) {
  useEffect(() => {
    if (disabled) return;
    const handler = (e: KeyboardEvent) => {
      const rating = Number(e.key);
      if (rating >= 1 && rating <= 4) onRate(rating as Rating);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onRate, disabled]);

  return (
    <div className="flex gap-2">
      {RATINGS.map(({ rating, label }) => (
        <Button key={rating} variant="outline" disabled={disabled} onClick={() => onRate(rating)}>
          {label} <span className="ml-1 text-muted-foreground">{rating}</span>
        </Button>
      ))}
    </div>
  );
}
