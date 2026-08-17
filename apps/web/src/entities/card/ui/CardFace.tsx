import type { Card } from "@/shared/api";
import { CardContent, Card as UICard } from "@/shared/ui/card";

export function CardFace({ card, revealed }: { card: Card; revealed: boolean }) {
  return (
    <UICard className="w-full max-w-md border-border bg-tint-lavender">
      <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
        <span className="text-5xl font-black tracking-tight text-foreground">{card.word}</span>
        {revealed && (
          <>
            {card.transcription && (
              <span className="rounded-full bg-background px-3 py-1 text-sm font-extrabold text-primary">
                /{card.transcription}/
              </span>
            )}
            <span className="mt-2 text-2xl font-black text-primary">{card.translation}</span>
          </>
        )}
      </CardContent>
    </UICard>
  );
}
