import { useMutation, useQueryClient } from "@tanstack/react-query";
import { reviewKeys } from "@/entities/card";
import { statsKeys } from "@/entities/stats";
import { apiClient, type ImportFormat, type ImportResult } from "@/shared/api";

export function useImportWords(deckId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      raw: string;
      format: ImportFormat;
      dryRun: boolean;
    }): Promise<ImportResult> => {
      const { data, error } = await apiClient.POST("/decks/{deck_id}/import", {
        params: { path: { deck_id: deckId } },
        body: { raw: input.raw, format: input.format, dry_run: input.dryRun },
      });
      if (error) throw new Error("Import failed");
      return data;
    },
    onSuccess: (result) => {
      if (result.committed) {
        qc.invalidateQueries({ queryKey: reviewKeys.queue(deckId) });
        qc.invalidateQueries({ queryKey: statsKeys.byDeck(deckId) });
      }
    },
  });
}
