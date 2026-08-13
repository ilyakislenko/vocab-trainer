import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, type Card, type Rating } from "@/shared/api";

export function useRecordReview(deckId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: { cardId: number; rating: Rating }): Promise<Card> => {
      const { data, error } = await apiClient.POST("/review", {
        body: { card_id: input.cardId, rating: input.rating },
      });
      if (error) throw new Error("Failed to record review");
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["review", "queue", deckId] });
      qc.invalidateQueries({ queryKey: ["stats", deckId] });
    },
  });
}
