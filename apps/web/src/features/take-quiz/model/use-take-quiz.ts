import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { CurriculumQuizGrade } from "@/shared/api";
import { apiClient } from "@/shared/api";

export function useTakeQuiz(moduleId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (
      answers: { item_id: string; given: string }[],
    ): Promise<CurriculumQuizGrade> => {
      const { data, error } = await apiClient.POST("/curriculum/quiz/grade", {
        body: { module_id: moduleId, answers },
      });
      if (error) throw new Error("Failed to grade quiz");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["curriculum", "map"] });
      qc.invalidateQueries({ queryKey: ["curriculum", "module", moduleId] });
    },
  });
}
