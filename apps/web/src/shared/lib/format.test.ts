import { describe, expect, it } from "vitest";
import { formatCount } from "./format";

describe("formatCount", () => {
  it("formats small counts without separators", () => {
    expect(formatCount(0, "en")).toBe("0");
    expect(formatCount(5, "en")).toBe("5");
    expect(formatCount(999, "ru")).toBe("999");
  });

  it("adds thousands separators in the English locale", () => {
    expect(formatCount(1000, "en")).toBe("1,000");
    expect(formatCount(12500, "en")).toBe("12,500");
  });

  it("adds thousands separators in the Russian locale", () => {
    expect(formatCount(1000, "ru")).toBe("1\u00a0000");
    expect(formatCount(12500, "ru")).toBe("12\u00a0500");
  });
});
