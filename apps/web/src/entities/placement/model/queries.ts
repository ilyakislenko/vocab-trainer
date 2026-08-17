import { useQuery } from "@tanstack/react-query";
import type { Placement } from "@/shared/api";
import { apiClient } from "@/shared/api";

export const placementKeys = {
  all: ["placement"] as const,
};

export function usePlacement() {
  return useQuery({
    queryKey: placementKeys.all,
    queryFn: async (): Promise<Placement> => {
      const { data, error } = await apiClient.GET("/placement");
      if (error) throw new Error("Failed to load placement");
      return data;
    },
  });
}
