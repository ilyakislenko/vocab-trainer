import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, type Deck } from "@/shared/api";

export const deckKeys = { all: ["decks"] as const };

export function useDecks() {
  return useQuery({
    queryKey: deckKeys.all,
    queryFn: async (): Promise<Deck[]> => {
      const { data, error } = await apiClient.GET("/decks");
      if (error) throw new Error("Failed to load decks");
      return data;
    },
  });
}

export function useCreateDeck() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (name: string): Promise<Deck> => {
      const { data, error } = await apiClient.POST("/decks", { body: { name } });
      if (error) throw new Error("Failed to create deck");
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: deckKeys.all }),
  });
}
