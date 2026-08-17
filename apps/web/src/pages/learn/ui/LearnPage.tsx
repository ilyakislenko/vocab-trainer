import { CurriculumMap } from "@/widgets/curriculum-map";
import { FocusList } from "@/widgets/focus-list";

export function LearnPage() {
  return (
    <div className="flex flex-col gap-8">
      <CurriculumMap />
      <FocusList />
    </div>
  );
}
