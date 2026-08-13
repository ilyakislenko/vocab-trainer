import { useMutation } from "@tanstack/react-query";
import { apiClient, type Feedback } from "@/shared/api";

export function useCheckSentence(cardId: number) {
  return useMutation({
    mutationFn: async (sentence: string): Promise<Feedback> => {
      const { data, error } = await apiClient.POST("/practice/check", {
        body: { card_id: cardId, sentence },
      });
      if (error) throw new Error("Check failed");
      return data;
    },
  });
}

export function useSuggestExample(cardId: number) {
  return useMutation({
    mutationFn: async (): Promise<string> => {
      const { data, error } = await apiClient.GET("/practice/example", {
        params: { query: { card_id: cardId } },
      });
      if (error) throw new Error("Example failed");
      return data.example;
    },
  });
}
