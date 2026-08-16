import { beforeEach, describe, expect, it, vi } from "vitest";
import { llmCache, withLlmCache } from "./llm-cache";

describe("llmCache", () => {
  beforeEach(async () => {
    await llmCache.clear();
  });

  it("returns undefined for a missing key", async () => {
    expect(await llmCache.get("missing")).toBeUndefined();
  });

  it("returns the stored value and keeps a second copy in memory", async () => {
    await llmCache.set("k", { meaning: "run fast" });
    expect(await llmCache.get("k")).toEqual({ meaning: "run fast" });
  });

  it("expires entries after the ttl", async () => {
    vi.useFakeTimers();
    try {
      await llmCache.set("k", "value", 1000);
      vi.advanceTimersByTime(1001);
      expect(await llmCache.get("k")).toBeUndefined();
    } finally {
      vi.useRealTimers();
    }
  });

  it("never expires when no ttl is given", async () => {
    vi.useFakeTimers();
    try {
      await llmCache.set("k", "value");
      vi.advanceTimersByTime(365 * 24 * 3600 * 1000);
      expect(await llmCache.get("k")).toBe("value");
    } finally {
      vi.useRealTimers();
    }
  });

  it("clears all entries", async () => {
    await llmCache.set("a", 1);
    await llmCache.set("b", 2);
    await llmCache.clear();
    expect(await llmCache.get("a")).toBeUndefined();
    expect(await llmCache.get("b")).toBeUndefined();
  });
});

describe("withLlmCache", () => {
  beforeEach(async () => {
    await llmCache.clear();
  });

  it("calls fetch only once and serves the cached value afterwards", async () => {
    const fetch = vi.fn(async () => ({ meaning: "hello" }));
    expect(await withLlmCache("hint:1", fetch)).toEqual({ meaning: "hello" });
    expect(await withLlmCache("hint:1", fetch)).toEqual({ meaning: "hello" });
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("propagates fetch errors and does not cache them", async () => {
    const fetch = vi.fn(async () => {
      throw new Error("boom");
    });
    await expect(withLlmCache("hint:1", fetch)).rejects.toThrow("boom");
    await expect(withLlmCache("hint:1", fetch)).rejects.toThrow("boom");
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("uses different keys independently", async () => {
    const fetch = vi.fn(async (key: string) => ({ key }));
    expect(await withLlmCache("a", () => fetch("a"))).toEqual({ key: "a" });
    expect(await withLlmCache("b", () => fetch("b"))).toEqual({ key: "b" });
    expect(await withLlmCache("a", () => fetch("a"))).toEqual({ key: "a" });
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
