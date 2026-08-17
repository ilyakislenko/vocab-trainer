import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CurriculumLesson,
  CurriculumMap,
  CurriculumModuleDetail,
  CurriculumModuleProgress,
} from "@/shared/api";
import { apiClient } from "@/shared/api";

export const curriculumKeys = {
  all: ["curriculum"] as const,
  map: () => [...curriculumKeys.all, "map"] as const,
  module: (moduleId: string) => [...curriculumKeys.all, "module", moduleId] as const,
  lesson: (moduleId: string) => [...curriculumKeys.all, "lesson", moduleId] as const,
};

export function useCurriculumMap() {
  return useQuery({
    queryKey: curriculumKeys.map(),
    queryFn: async (): Promise<CurriculumMap> => {
      const { data, error } = await apiClient.GET("/curriculum");
      if (error) throw new Error("Failed to load curriculum");
      return data;
    },
  });
}

export function useModuleDetail(moduleId: string) {
  return useQuery({
    queryKey: curriculumKeys.module(moduleId),
    queryFn: async (): Promise<CurriculumModuleDetail> => {
      const { data, error } = await apiClient.GET("/curriculum/modules/{module_id}", {
        params: { path: { module_id: moduleId } },
      });
      if (error) throw new Error("Failed to load module");
      return data;
    },
  });
}

export function useLesson(moduleId: string) {
  return useQuery({
    queryKey: curriculumKeys.lesson(moduleId),
    queryFn: async (): Promise<CurriculumLesson> => {
      const { data, error } = await apiClient.GET("/curriculum/lessons/{module_id}", {
        params: { path: { module_id: moduleId } },
      });
      if (error) throw new Error("Failed to load lesson");
      return data;
    },
  });
}

export function useMarkLessonRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (moduleId: string): Promise<CurriculumModuleProgress> => {
      const { data, error } = await apiClient.POST("/curriculum/lessons/{module_id}/read", {
        params: { path: { module_id: moduleId } },
      });
      if (error) throw new Error("Failed to mark lesson read");
      return data;
    },
    onSuccess: (_data, moduleId) => {
      qc.invalidateQueries({ queryKey: curriculumKeys.map() });
      qc.invalidateQueries({ queryKey: curriculumKeys.module(moduleId) });
    },
  });
}
