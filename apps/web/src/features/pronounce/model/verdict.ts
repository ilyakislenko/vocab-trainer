export type PronounceVerdict = "good" | "fair" | "weak";

export function verdictTone(verdict: PronounceVerdict): PronounceVerdict {
  return verdict;
}

export function overallPercent(score: number): number {
  return Math.round(score * 100);
}

// Display curve for the headline score only. Raw GOP posteriors are compressed —
// a well-said phoneme rarely reaches 1.0 — so the plain average reads low (~76%)
// even when every phoneme is green. This monotonic S-curve spreads the scale so
// good pronunciation reads higher and poor stays low; it is order-preserving and
// does NOT touch the per-phoneme scores or verdicts.
export function overallScorePercent(raw: number): number {
  const x = Math.min(1, Math.max(0, raw));
  if (x === 0 || x === 1) return Math.round(x * 100);
  const a = 1.5;
  const curved = x ** a / (x ** a + (1 - x) ** a);
  return Math.round(curved * 100);
}
