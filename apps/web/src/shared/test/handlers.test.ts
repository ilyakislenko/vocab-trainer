import { describe, expect, it } from "vitest";
import { apiClient } from "@/shared/api";

describe("msw handlers", () => {
  it("intercepts GET /decks with the default handler", async () => {
    const { data } = await apiClient.GET("/decks");
    expect(data).toEqual([{ id: 1, name: "Sample" }]);
  });
});
