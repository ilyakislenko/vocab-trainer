import { describe, expect, it } from "vitest";
import { overallPercent, overallScorePercent } from "./verdict";

describe("overallScorePercent (headline display curve)", () => {
  it("keeps the endpoints exact", () => {
    expect(overallScorePercent(0)).toBe(0);
    expect(overallScorePercent(1)).toBe(100);
    expect(overallScorePercent(0.5)).toBe(50);
  });

  it("lifts good pronunciation and keeps poor low", () => {
    // "all green" ~0.76 raw reads as a satisfying ~85%…
    expect(overallScorePercent(0.76)).toBeGreaterThanOrEqual(83);
    expect(overallScorePercent(0.76)).toBeLessThanOrEqual(88);
    // …while a weak attempt ~0.33 stays low (and below its raw percent).
    expect(overallScorePercent(0.33)).toBeLessThan(overallPercent(0.33));
  });

  it("is monotonic and clamps out-of-range input", () => {
    expect(overallScorePercent(0.9)).toBeGreaterThan(overallScorePercent(0.6));
    expect(overallScorePercent(-1)).toBe(0);
    expect(overallScorePercent(2)).toBe(100);
  });
});
