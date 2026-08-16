import { useMutation } from "@tanstack/react-query";
import { apiClient, type Feedback } from "@/shared/api";

export function useCheckSentence(cardId: number | null) {
  return useMutation({
    mutationFn: async (sentence: string): Promise<Feedback> => {
      if (cardId === null) throw new Error("No card to check against");
      const { data, error } = await apiClient.POST("/practice/check", {
        body: { card_id: cardId, sentence },
      });
      if (error) throw new Error("Check failed");
      return data;
    },
  });
}
