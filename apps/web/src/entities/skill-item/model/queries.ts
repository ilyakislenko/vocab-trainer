import { useQuery } from "@tanstack/react-query";
import type { CurriculumSkillItem, CurriculumSkillReview } from "@/shared/api";
import { apiClient } from "@/shared/api";

export const skillKeys = {
  all: ["review", "skills"] as const,
  queue: () => [...skillKeys.all, "queue"] as const,
  focus: () => ["session", "focus"] as const,
};

export function useSkillReviewQueue(limit = 20, enabled = true) {
  return useQuery({
    queryKey: skillKeys.queue(),
    enabled,
    queryFn: async (): Promise<CurriculumSkillReview[]> => {
      const { data, error } = await apiClient.GET("/review/skills/queue", {
        params: { query: { limit } },
      });
      if (error) throw new Error("Failed to load skill review queue");
      return data;
    },
  });
}

export function useFocusLeeches(limit = 3, enabled = true) {
  return useQuery({
    queryKey: skillKeys.focus(),
    enabled,
    queryFn: async (): Promise<CurriculumSkillItem[]> => {
      const { data, error } = await apiClient.GET("/session/focus", {
        params: { query: { limit } },
      });
      if (error) throw new Error("Failed to load focus list");
      return data;
    },
  });
}
