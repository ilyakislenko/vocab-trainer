import { useQuery } from "@tanstack/react-query";
import type { TodaySession } from "@/shared/api";
import { apiClient } from "@/shared/api";

export const sessionKeys = {
  today: ["session", "today"] as const,
};

export function useTodaySession() {
  return useQuery({
    queryKey: sessionKeys.today,
    queryFn: async (): Promise<TodaySession> => {
      const { data, error } = await apiClient.GET("/session/today");
      if (error) throw new Error("Failed to load today session");
      return data;
    },
  });
}
