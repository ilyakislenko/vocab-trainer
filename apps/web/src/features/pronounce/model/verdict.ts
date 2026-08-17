export type PronounceVerdict = "good" | "fair" | "weak";

export function verdictTone(verdict: PronounceVerdict): PronounceVerdict {
  return verdict;
}

export function overallPercent(score: number): number {
  return Math.round(score * 100);
}
