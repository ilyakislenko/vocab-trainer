import { useParams } from "react-router-dom";
import { LessonReader } from "@/widgets/lesson-reader";

export function LessonPage() {
  const { moduleId } = useParams<{ moduleId: string }>();
  if (!moduleId) return null;
  return <LessonReader moduleId={moduleId} />;
}
