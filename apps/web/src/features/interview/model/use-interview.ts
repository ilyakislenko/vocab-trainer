import { useMutation } from "@tanstack/react-query";
import { apiClient, type InterviewMessage, type InterviewOut } from "@/shared/api";

export type InterviewLang = "ru" | "en";
export type InterviewDifficulty = "junior" | "middle" | "senior";

export function useInterview() {
  return useMutation({
    mutationFn: async ({
      topic,
      lang,
      difficulty,
      mode,
      usedQuestionIds,
      messages,
    }: {
      topic: string;
      lang: InterviewLang;
      difficulty: InterviewDifficulty;
      mode?: "auto" | "next" | "random";
      usedQuestionIds: number[];
      messages: InterviewMessage[];
    }): Promise<InterviewOut> => {
      const { data, error } = await apiClient.POST("/practice/interview", {
        body: {
          topic,
          lang,
          difficulty,
          mode: mode ?? "auto",
          used_question_ids: usedQuestionIds,
          messages,
        },
      });
      if (error) throw new Error("Interview failed");
      return data;
    },
  });
}
