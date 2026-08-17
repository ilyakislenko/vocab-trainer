import { useMutation, useQueryClient } from "@tanstack/react-query";
import { skillKeys } from "@/entities/skill-item";
import { apiClient, type CurriculumSkillItem, type Rating } from "@/shared/api";

export function useRecordSkillReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      skillItemId: number;
      rating: Rating;
    }): Promise<CurriculumSkillItem> => {
      const { data, error } = await apiClient.POST("/review/skills", {
        body: { skill_item_id: input.skillItemId, rating: input.rating },
      });
      if (error) throw new Error("Failed to record skill review");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: skillKeys.queue() });
      qc.invalidateQueries({ queryKey: skillKeys.focus() });
    },
  });
}
