import { describe, expect, it } from "vitest";
import { INTERVIEW_PHRASES, type PhraseCategory, phrasesByCategory } from "./phrases";

const CATEGORIES: PhraseCategory[] = [
  "react",
  "typescript",
  "frontend",
  "ai",
  "backend",
  "behavioral",
];

describe("INTERVIEW_PHRASES", () => {
  it("has enough phrases spread across every category", () => {
    expect(INTERVIEW_PHRASES.length).toBeGreaterThanOrEqual(30);
    for (const category of CATEGORIES) {
      expect(phrasesByCategory(category).length).toBeGreaterThanOrEqual(3);
    }
  });

  it("gives every phrase a unique id", () => {
    const ids = INTERVIEW_PHRASES.map((phrase) => phrase.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("only uses valid categories", () => {
    for (const phrase of INTERVIEW_PHRASES) {
      expect(CATEGORIES).toContain(phrase.category);
    }
  });

  it("keeps every phrase a single sentence of 3-20 words", () => {
    for (const phrase of INTERVIEW_PHRASES) {
      expect(phrase.text).not.toBe("");
      const words = phrase.text.trim().split(/\s+/);
      expect(words.length).toBeGreaterThanOrEqual(3);
      expect(words.length).toBeLessThanOrEqual(20);
    }
  });
});
