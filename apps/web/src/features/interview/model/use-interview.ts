import { useMutation } from "@tanstack/react-query";
import { apiClient, type InterviewMessage, type InterviewOut } from "@/shared/api";

export type InterviewLang = "ru" | "en";

export function useInterview() {
  return useMutation({
    mutationFn: async ({
      topic,
      lang,
      mode,
      usedQuestionIds,
      messages,
    }: {
      topic: string;
      lang: InterviewLang;
      mode?: "auto" | "next" | "random";
      usedQuestionIds: number[];
      messages: InterviewMessage[];
    }): Promise<InterviewOut> => {
      const { data, error } = await apiClient.POST("/practice/interview", {
        body: {
          topic,
          lang,
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
