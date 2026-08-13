import type { Card } from "@/shared/api";
import { CardContent, Card as UICard } from "@/shared/ui/card";

export function CardFace({ card, revealed }: { card: Card; revealed: boolean }) {
  return (
    <UICard className="w-full max-w-md">
      <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
        <span className="text-3xl font-semibold">{card.word}</span>
        {revealed && (
          <>
            {card.transcription && (
              <span className="text-muted-foreground">/{card.transcription}/</span>
            )}
            <span className="text-xl">{card.translation}</span>
          </>
        )}
      </CardContent>
    </UICard>
  );
}
