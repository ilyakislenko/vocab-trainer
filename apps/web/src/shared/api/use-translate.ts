import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/shared/api";
import { withLlmCache } from "@/shared/lib/llm-cache";

export const translateKeys = {
  sentence: (text: string) => ["translate", text] as const,
};

const translateCacheKey = (text: string) => `translate:${text}`;

export function useTranslateSentence(text: string) {
  return useQuery({
    queryKey: translateKeys.sentence(text),
    enabled: text.length > 0,
    staleTime: Infinity,
    queryFn: async () =>
      withLlmCache(translateCacheKey(text), async () => {
        const { data, error } = await apiClient.GET("/practice/translate", {
          params: { query: { text } },
        });
        if (error) throw new Error("Translation failed");
        return data;
      }),
  });
}
