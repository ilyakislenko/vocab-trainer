import { useQuery } from "@tanstack/react-query";
import { apiClient, type WordHint } from "@/shared/api";
import { withLlmCache } from "@/shared/lib/llm-cache";

export const hintKeys = {
  detail: (cardId: number) => ["practice", "hint", cardId] as const,
};

const hintCacheKey = (cardId: number) => `hint:${cardId}`;

export function useWordHint(cardId: number) {
  return useQuery({
    queryKey: hintKeys.detail(cardId),
    staleTime: Infinity,
    queryFn: async (): Promise<WordHint> =>
      withLlmCache(hintCacheKey(cardId), async () => {
        const { data, error } = await apiClient.GET("/practice/hint", {
          params: { query: { card_id: cardId } },
        });
        if (error) throw new Error("Hint failed");
        return data;
      }),
  });
}
