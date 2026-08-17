import { useCallback, useEffect, useRef, useState } from "react";
import type { InterviewMessage, InterviewOut } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { speak } from "@/shared/lib/speech";
import { type InterviewDifficulty, type InterviewLang, useInterview } from "./use-interview";

export type SceneKey = "office" | "cafe" | "park" | "night";

export type InterviewView = "chat" | "call";

export type SessionPhase = "setup" | "active" | "summary";

export type SessionConfig = {
  topic: string;
  difficulty: InterviewDifficulty;
  questionCount: number; // 0 = unlimited
  view: InterviewView;
  lang: InterviewLang;
  scene: SceneKey;
};

export type ChatMessage = {
  id: number;
  role: "interviewer" | "user";
  text: string;
  kind?: "feedback";
  verdict?: "ok" | "needs_work" | null;
  corrected?: string | null;
};

export type SessionStats = {
  questions: number;
  ok: number;
  needsWork: number;
  corrections: string[];
};

export type VerdictReaction = "happy" | "sad";

export const INTERVIEW_TOPICS = ["React", "TypeScript", "Frontend", "Backend"] as const;

export const INTERVIEW_DIFFICULTIES: InterviewDifficulty[] = ["junior", "middle", "senior"];

export const QUESTION_COUNTS = [3, 5, 10, 0] as const;

export const SCENES: SceneKey[] = ["office", "cafe", "park", "night"];

const DEFAULT_CONFIG: SessionConfig = {
  topic: "React",
  difficulty: "middle",
  questionCount: 0,
  view: "chat",
  lang: "en",
  scene: "office",
};

const EMPTY_STATS: SessionStats = { questions: 0, ok: 0, needsWork: 0, corrections: [] };

export function useInterviewSession(initialTopic?: string) {
  const { t } = useI18n();
  const interview = useInterview();
  const [phase, setPhase] = useState<SessionPhase>("setup");
  const [config, setConfig] = useState<SessionConfig>({
    ...DEFAULT_CONFIG,
    ...(initialTopic ? { topic: initialTopic } : {}),
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [stats, setStats] = useState<SessionStats>(EMPTY_STATS);
  const [reaction, setReaction] = useState<VerdictReaction | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const usedQuestionIdsRef = useRef<number[]>([]);
  const nextIdRef = useRef(0);

  const { mutateAsync, isPending } = interview;

  useEffect(() => {
    if (phase !== "active") return;
    const id = window.setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => window.clearInterval(id);
  }, [phase]);

  const addMessage = useCallback((message: Omit<ChatMessage, "id">) => {
    const id = nextIdRef.current++;
    setMessages((prev) => [...prev, { ...message, id }]);
  }, []);

  const speakQuestion = useCallback((text: string) => {
    setSpeaking(true);
    speak(text, () => setSpeaking(false));
  }, []);

  const countQuestion = useCallback((questionId: number | null | undefined) => {
    if (questionId == null) return;
    usedQuestionIdsRef.current = [...new Set([...usedQuestionIdsRef.current, questionId])];
    setStats((prev) => ({ ...prev, questions: usedQuestionIdsRef.current.length }));
  }, []);

  const finishWhenLimitReached = useCallback(() => {
    if (config.questionCount > 0 && usedQuestionIdsRef.current.length >= config.questionCount) {
      setPhase("summary");
    }
  }, [config.questionCount]);

  const appendInterviewerTurn = useCallback(
    (result: InterviewOut) => {
      if (result.feedback) {
        addMessage({
          role: "interviewer",
          kind: "feedback",
          text: result.feedback,
          verdict: result.verdict,
          corrected: result.corrected,
        });
        if (result.verdict === "ok") {
          setStats((prev) => ({ ...prev, ok: prev.ok + 1 }));
          setReaction("happy");
        } else if (result.verdict === "needs_work") {
          setStats((prev) => ({
            ...prev,
            needsWork: prev.needsWork + 1,
            corrections:
              result.corrected != null ? [...prev.corrections, result.corrected] : prev.corrections,
          }));
          setReaction("sad");
        }
      }
      if (result.question) {
        addMessage({ role: "interviewer", text: result.question });
        countQuestion(result.question_id);
        speakQuestion(result.question);
      }
    },
    [addMessage, countQuestion, speakQuestion],
  );

  const updateConfig = useCallback((patch: Partial<SessionConfig>) => {
    setConfig((prev) => ({ ...prev, ...patch }));
  }, []);

  const start = useCallback(
    async (cfg: SessionConfig) => {
      setConfig(cfg);
      setPhase("active");
      setMessages([]);
      setStats(EMPTY_STATS);
      setReaction(null);
      setElapsed(0);
      setSpeaking(false);
      usedQuestionIdsRef.current = [];
      nextIdRef.current = 0;
      try {
        const result = await mutateAsync({
          topic: cfg.topic,
          lang: cfg.lang,
          difficulty: cfg.difficulty,
          usedQuestionIds: [],
          messages: [],
        });
        addMessage({ role: "interviewer", text: result.question });
        countQuestion(result.question_id);
        speakQuestion(result.question);
        finishWhenLimitReached();
      } catch {
        addMessage({ role: "interviewer", text: t("interview.error") });
      }
    },
    [mutateAsync, addMessage, countQuestion, speakQuestion, finishWhenLimitReached, t],
  );

  const advance = useCallback(
    async (answer: string) => {
      const userMsg = answer.trim();
      if (!userMsg || isPending) return;
      setReaction(null);
      addMessage({ role: "user", text: userMsg });
      const history: InterviewMessage[] = [
        ...messages.map((m) => ({ role: m.role, content: m.text })),
        { role: "user", content: userMsg },
      ];
      try {
        const result = await mutateAsync({
          topic: config.topic,
          lang: config.lang,
          difficulty: config.difficulty,
          usedQuestionIds: usedQuestionIdsRef.current,
          messages: history,
        });
        appendInterviewerTurn(result);
        finishWhenLimitReached();
      } catch {
        addMessage({ role: "interviewer", text: t("interview.error") });
      }
    },
    [
      mutateAsync,
      addMessage,
      appendInterviewerTurn,
      finishWhenLimitReached,
      config,
      isPending,
      messages,
      t,
    ],
  );

  const requestBank = useCallback(
    async (mode: "next" | "random") => {
      if (isPending || !config.topic) return;
      setReaction(null);
      try {
        const result = await mutateAsync({
          topic: config.topic,
          lang: config.lang,
          difficulty: config.difficulty,
          mode,
          usedQuestionIds: usedQuestionIdsRef.current,
          messages: [],
        });
        appendInterviewerTurn(result);
        finishWhenLimitReached();
      } catch {
        addMessage({ role: "interviewer", text: t("interview.error") });
      }
    },
    [mutateAsync, addMessage, appendInterviewerTurn, finishWhenLimitReached, config, isPending, t],
  );

  const steerTopic = useCallback(
    (customTopic: string) => {
      const topicText = customTopic.trim();
      if (!topicText || isPending) return;
      const phrase =
        config.lang === "ru"
          ? `Давай поговорим про ${topicText}.`
          : `Let's talk about ${topicText}.`;
      void advance(phrase);
    },
    [advance, config.lang, isPending],
  );

  const end = useCallback(() => {
    setPhase("summary");
  }, []);

  const backToSetup = useCallback(() => {
    setPhase("setup");
    setMessages([]);
    setStats(EMPTY_STATS);
    setReaction(null);
    setElapsed(0);
    setSpeaking(false);
    usedQuestionIdsRef.current = [];
    nextIdRef.current = 0;
  }, []);

  return {
    phase,
    config,
    updateConfig,
    messages,
    stats,
    reaction,
    elapsed,
    speaking,
    isPending,
    start,
    advance,
    requestBank,
    steerTopic,
    end,
    backToSetup,
  };
}
