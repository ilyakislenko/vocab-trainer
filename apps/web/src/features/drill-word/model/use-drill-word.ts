import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/shared/api";

export function useDrillWord(cardId: number) {
  return useMutation({
    mutationFn: async (
      message: string,
    ): Promise<{ response: string; question?: string | null }> => {
      const { data, error } = await apiClient.POST("/practice/drill", {
        body: { card_id: cardId, message },
      });
      if (error) throw new Error("Drill failed");
      return data;
    },
  });
}
