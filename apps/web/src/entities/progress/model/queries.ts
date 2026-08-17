import { useQuery } from "@tanstack/react-query";
import type { Progress } from "@/shared/api";
import { apiClient } from "@/shared/api";

export const progressKeys = {
  report: ["progress", "report"] as const,
};

export function useProgress() {
  return useQuery({
    queryKey: progressKeys.report,
    queryFn: async (): Promise<Progress> => {
      const { data, error } = await apiClient.GET("/progress");
      if (error) throw new Error("Failed to load progress");
      return data;
    },
  });
}
