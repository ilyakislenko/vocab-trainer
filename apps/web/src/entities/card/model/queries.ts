import { useQuery } from "@tanstack/react-query";
import { apiClient, type Card } from "@/shared/api";

export const reviewKeys = {
  queue: (deckId: number) => ["review", "queue", deckId] as const,
};

export function useReviewQueue(deckId: number | null, limit = 20) {
  return useQuery({
    queryKey: deckId === null ? ["review", "queue", "none"] : reviewKeys.queue(deckId),
    enabled: deckId !== null,
    queryFn: async (): Promise<Card[]> => {
      const { data, error } = await apiClient.GET("/review/queue", {
        params: { query: { deck_id: deckId as number, limit } },
      });
      if (error) throw new Error("Failed to load review queue");
      return data;
    },
  });
}
