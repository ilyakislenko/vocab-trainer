import { Navigate } from "react-router-dom";
import { useCurriculumMap } from "@/entities/curriculum";
import { CurriculumMap } from "@/widgets/curriculum-map";
import { FocusList } from "@/widgets/focus-list";

export function LearnPage() {
  const map = useCurriculumMap();

  // Onboarding routes a new learner through placement first (§16): the map is
  // only shown once a level has been estimated.
  if (map.isLoading) return null;
  if (map.data && !map.data.placement_level) {
    return <Navigate to="/placement" replace />;
  }

  return (
    <div className="flex flex-col gap-8">
      <CurriculumMap />
      <FocusList />
    </div>
  );
}
