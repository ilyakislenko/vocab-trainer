import { useQuery } from "@tanstack/react-query";
import { apiClient, type Card, type ReviewSummary } from "@/shared/api";

export const reviewKeys = {
  queue: (deckId: number) => ["review", "queue", deckId] as const,
  summary: (deckId: number) => ["review", "summary", deckId] as const,
};

const PAGE_SIZE = 500;

export function useReviewQueue(deckId: number | null, limit = 20, enabled = true) {
  return useQuery({
    queryKey: deckId === null ? ["review", "queue", "none"] : reviewKeys.queue(deckId),
    enabled: enabled && deckId !== null,
    queryFn: async (): Promise<Card[]> => {
      const { data, error } = await apiClient.GET("/review/queue", {
        params: { query: { deck_id: deckId as number, limit } },
      });
      if (error) throw new Error("Failed to load review queue");
      return data;
    },
  });
}

export function useReviewSummary(deckId: number | null, enabled = true) {
  return useQuery({
    queryKey: deckId === null ? ["review", "summary", "none"] : reviewKeys.summary(deckId),
    enabled: enabled && deckId !== null,
    queryFn: async (): Promise<ReviewSummary> => {
      const { data, error } = await apiClient.GET("/review/summary", {
        params: { query: { deck_id: deckId as number } },
      });
      if (error) throw new Error("Failed to load review summary");
      return data;
    },
  });
}

export function useDeckCards(deckId: number | null, enabled = true) {
  return useQuery({
    queryKey: deckId === null ? ["deck", "cards", "none"] : ["deck", "cards", deckId],
    enabled: enabled && deckId !== null,
    queryFn: async (): Promise<Card[]> => {
      const all: Card[] = [];
      for (let offset = 0; ; offset += PAGE_SIZE) {
        const { data, error } = await apiClient.GET("/decks/{deck_id}/cards", {
          params: {
            path: { deck_id: deckId as number },
            query: { limit: PAGE_SIZE, offset },
          },
        });
        if (error) throw new Error("Failed to load deck cards");
        all.push(...data);
        if (data.length < PAGE_SIZE) break;
      }
      return all;
    },
  });
}

export function useTopicWords(deckId: number | null, topic: string | null) {
  return useQuery({
    queryKey:
      deckId === null || topic === null
        ? ["practice", "topic", "none"]
        : ["practice", "topic", deckId, topic],
    enabled: deckId !== null && topic !== null && topic.length > 0,
    queryFn: async (): Promise<Card[]> => {
      const { data, error } = await apiClient.GET("/practice/topic", {
        params: { query: { deck_id: deckId as number, topic: topic as string, limit: 20 } },
      });
      if (error) throw new Error("Failed to load topic words");
      return data;
    },
  });
}
