import type { components } from "./schema";

export type Deck = components["schemas"]["DeckOut"];
export type Card = components["schemas"]["CardOut"];
export type Stats = components["schemas"]["StatsOut"];
export type ImportResult = components["schemas"]["ImportOut"];
export type RowError = components["schemas"]["RowErrorOut"];
export type ImportFormat = "csv" | "markdown";
export type Rating = 1 | 2 | 3 | 4;
export type Feedback = components["schemas"]["FeedbackOut"];
export type WordHint = components["schemas"]["WordHintOut"];
export type InterviewOut = components["schemas"]["InterviewOut"];
export type InterviewMessage = components["schemas"]["InterviewMessage"];
