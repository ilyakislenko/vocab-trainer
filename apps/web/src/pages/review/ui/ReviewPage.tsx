import { useProgress } from "@/entities/progress";
import { NoDeck } from "@/widgets/no-deck";
import { Onboarding } from "@/widgets/onboarding";
import { ReviewSession } from "@/widgets/review-session";

export function ReviewPage({ deckId }: { deckId: number | null }) {
  const progress = useProgress();
  const firstRun = progress.data?.has_reviewed === false;

  if (deckId === null) return <NoDeck />;

  return (
    <div className="flex flex-col gap-6">
      {firstRun && <Onboarding />}
      <ReviewSession key={deckId} deckId={deckId} />
    </div>
  );
}
