import { describe, expect, it } from "vitest";
import { apiClient } from "./client";

describe("apiClient", () => {
  it("exposes typed GET and POST methods", () => {
    expect(typeof apiClient.GET).toBe("function");
    expect(typeof apiClient.POST).toBe("function");
  });
});
