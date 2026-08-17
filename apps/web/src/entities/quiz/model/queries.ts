import { useQuery } from "@tanstack/react-query";
import type { CurriculumQuiz } from "@/shared/api";
import { apiClient } from "@/shared/api";

export const quizKeys = {
  all: ["curriculum", "quiz"] as const,
  quiz: (moduleId: string) => [...quizKeys.all, moduleId] as const,
};

export function useQuiz(moduleId: string) {
  return useQuery({
    queryKey: quizKeys.quiz(moduleId),
    queryFn: async (): Promise<CurriculumQuiz> => {
      const { data, error } = await apiClient.GET("/curriculum/modules/{module_id}/quiz", {
        params: { path: { module_id: moduleId } },
      });
      if (error) throw new Error("Failed to load quiz");
      return data;
    },
  });
}
