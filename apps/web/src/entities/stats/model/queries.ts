import { useQuery } from "@tanstack/react-query";
import { apiClient, type Stats } from "@/shared/api";

export const statsKeys = { byDeck: (deckId: number) => ["stats", deckId] as const };

export function useStats(deckId: number | null) {
  return useQuery({
    queryKey: deckId === null ? ["stats", "none"] : statsKeys.byDeck(deckId),
    enabled: deckId !== null,
    queryFn: async (): Promise<Stats> => {
      const { data, error } = await apiClient.GET("/stats", {
        params: { query: { deck_id: deckId as number } },
      });
      if (error) throw new Error("Failed to load stats");
      return data;
    },
  });
}
