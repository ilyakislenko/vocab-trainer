import { Onboarding } from "@/widgets/onboarding";
import { ReviewSession } from "@/widgets/review-session";

export function ReviewPage({ deckId }: { deckId: number | null }) {
  if (deckId === null) return <Onboarding />;
  return <ReviewSession key={deckId} deckId={deckId} />;
}
