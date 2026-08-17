import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { PlacementAnswer, PlacementGrade } from "@/shared/api";
import { apiClient } from "@/shared/api";

export function useTakePlacement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (answers: PlacementAnswer[]): Promise<PlacementGrade> => {
      const { data, error } = await apiClient.POST("/placement/grade", {
        body: { answers },
      });
      if (error) throw new Error("Failed to grade placement");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["curriculum", "map"] });
    },
  });
}
