import { describe, expect, it } from "vitest";
import { apiClient } from "@/shared/api";

describe("practice api", () => {
  it("checks a sentence via the typed client", async () => {
    const { data } = await apiClient.POST("/practice/check", {
      body: { card_id: 1, sentence: "I run daily." },
    });
    expect(data?.verdict).toBe("ok");
  });
  it("fetches an example", async () => {
    const { data } = await apiClient.GET("/practice/example", {
      params: { query: { card_id: 1 } },
    });
    expect(data?.example).toContain("runs");
  });
});
