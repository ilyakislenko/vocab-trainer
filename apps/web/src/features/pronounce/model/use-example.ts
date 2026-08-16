import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api";
import { withLlmCache } from "@/shared/lib/llm-cache";

const exampleCacheKey = (cardId: number) => `example:${cardId}`;

export function useExample(cardId: number | null) {
  return useQuery({
    queryKey: ["practice", "example", cardId],
    staleTime: Infinity,
    enabled: cardId !== null,
    queryFn: async (): Promise<string | null> => {
      if (cardId === null) return null;
      return withLlmCache(exampleCacheKey(cardId), async () => {
        const { data, error } = await apiClient.GET("/practice/example", {
          params: { query: { card_id: cardId } },
        });
        if (error) throw new Error("Example failed");
        return data.example;
      });
    },
  });
}
