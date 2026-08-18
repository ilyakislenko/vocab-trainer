export type PhraseCategory = "react" | "typescript" | "frontend" | "ai" | "backend" | "behavioral";

export interface InterviewPhrase {
  id: string;
  category: PhraseCategory;
  text: string;
}

export const INTERVIEW_PHRASES: InterviewPhrase[] = [
  {
    id: "react-1",
    category: "react",
    text: "I optimize re-renders with memoization and stable keys.",
  },
  {
    id: "react-2",
    category: "react",
    text: "I lift state up only when two components truly share it.",
  },
  {
    id: "react-3",
    category: "react",
    text: "I use custom hooks to isolate effects and reuse async logic.",
  },
  {
    id: "react-4",
    category: "react",
    text: "I render lists with stable keys and virtualize long ones.",
  },
  {
    id: "react-5",
    category: "react",
    text: "I split large components by responsibility, not by size alone.",
  },
  {
    id: "react-6",
    category: "react",
    text: "I prefer controlled inputs and keep form state in one place.",
  },
  {
    id: "typescript-1",
    category: "typescript",
    text: "I model the domain with discriminated unions and narrow at the boundaries.",
  },
  {
    id: "typescript-2",
    category: "typescript",
    text: "I type the API layer so a schema change breaks the build early.",
  },
  {
    id: "typescript-3",
    category: "typescript",
    text: "I write generics that stay readable instead of over-abstracting.",
  },
  {
    id: "typescript-4",
    category: "typescript",
    text: "I use satisfies to keep literals while preserving their exact types.",
  },
  {
    id: "typescript-5",
    category: "typescript",
    text: "I treat unknown as the honest default for untrusted data.",
  },
  {
    id: "typescript-6",
    category: "typescript",
    text: "I prefer explicit function types over hidden structural inference.",
  },
  {
    id: "frontend-1",
    category: "frontend",
    text: "I care about accessibility, semantic HTML, and keyboard navigation.",
  },
  {
    id: "frontend-2",
    category: "frontend",
    text: "I measure performance with the browser profiler before optimizing.",
  },
  {
    id: "frontend-3",
    category: "frontend",
    text: "I keep layouts responsive without pixel-perfect duplication.",
  },
  {
    id: "frontend-4",
    category: "frontend",
    text: "I build design tokens so dark mode stays consistent everywhere.",
  },
  {
    id: "frontend-5",
    category: "frontend",
    text: "I test user flows, not just component snapshots.",
  },
  {
    id: "frontend-6",
    category: "frontend",
    text: "I optimize the critical path before touching the bundle size.",
  },
  {
    id: "ai-1",
    category: "ai",
    text: "I've integrated large language model APIs behind a provider interface.",
  },
  {
    id: "ai-2",
    category: "ai",
    text: "I stream tokens to the client and handle provider failures gracefully.",
  },
  {
    id: "ai-3",
    category: "ai",
    text: "I evaluate prompts with a small labeled set before shipping.",
  },
  {
    id: "ai-4",
    category: "ai",
    text: "I design retrieval to return only what the model actually needs.",
  },
  {
    id: "ai-5",
    category: "ai",
    text: "I keep guardrails around model output so the UI stays safe.",
  },
  { id: "ai-6", category: "ai", text: "I treat context windows as a budget, not a limit." },
  {
    id: "backend-1",
    category: "backend",
    text: "I design REST endpoints to be stateless and paginated.",
  },
  {
    id: "backend-2",
    category: "backend",
    text: "I put business rules in the domain layer, not in the controllers.",
  },
  {
    id: "backend-3",
    category: "backend",
    text: "I write migrations that roll back cleanly and never lose data.",
  },
  { id: "backend-4", category: "backend", text: "I cache aggressively but invalidate with care." },
  {
    id: "backend-5",
    category: "backend",
    text: "I make services observable with structured logs and metrics.",
  },
  {
    id: "backend-6",
    category: "backend",
    text: "I prefer idempotent writes for retries that can't duplicate work.",
  },
  {
    id: "behavioral-1",
    category: "behavioral",
    text: "I'd start by clarifying the requirements and the success criteria.",
  },
  {
    id: "behavioral-2",
    category: "behavioral",
    text: "When I disagree, I bring data and stay focused on the goal.",
  },
  {
    id: "behavioral-3",
    category: "behavioral",
    text: "I ask for a code review early and treat feedback as fuel.",
  },
  {
    id: "behavioral-4",
    category: "behavioral",
    text: "I break ambiguous tasks into small steps with visible results.",
  },
  {
    id: "behavioral-5",
    category: "behavioral",
    text: "I share progress early so surprises happen before they cost time.",
  },
  {
    id: "behavioral-6",
    category: "behavioral",
    text: "I take ownership of outages until the root cause is understood.",
  },
];

export function phrasesByCategory(category: PhraseCategory): InterviewPhrase[] {
  return INTERVIEW_PHRASES.filter((phrase) => phrase.category === category);
}
