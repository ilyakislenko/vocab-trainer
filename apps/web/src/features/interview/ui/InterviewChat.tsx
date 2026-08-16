import { Mic, MicOff, PhoneOff, Video, VideoOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { InterviewMessage, InterviewOut } from "@/shared/api";
import { useI18n } from "@/shared/lib/i18n";
import { speak } from "@/shared/lib/speech";
import { Button } from "@/shared/ui/button";
import { HoverableSentence } from "@/shared/ui/hoverable-sentence";
import { Loader } from "@/shared/ui/loader";
import { type Emotion, Mascot } from "@/shared/ui/mascot";
import { MicButton } from "@/shared/ui/mic-button";
import { Textarea } from "@/shared/ui/textarea";
import { type InterviewLang, useInterview } from "../model/use-interview";
import { LocationScene, type SceneKey } from "./call-scenes";

type ChatMessage = {
  id: number;
  role: "interviewer" | "user";
  text: string;
};

type ViewMode = "chat" | "call";

const TOPICS = [
  { value: "React", labelKey: "interview.topicReact" },
  { value: "TypeScript", labelKey: "interview.topicTypeScript" },
  { value: "Frontend", labelKey: "interview.topicFrontend" },
  { value: "Backend", labelKey: "interview.topicBackend" },
];

const LANGS: { value: InterviewLang; labelKey: string }[] = [
  { value: "en", labelKey: "interview.langEn" },
  { value: "ru", labelKey: "interview.langRu" },
];

const SCENES: { value: SceneKey; labelKey: string }[] = [
  { value: "office", labelKey: "interview.callSceneOffice" },
  { value: "cafe", labelKey: "interview.callSceneCafe" },
  { value: "park", labelKey: "interview.callScenePark" },
  { value: "night", labelKey: "interview.callSceneNight" },
];

export function InterviewChat({
  topic,
  onTopicChange,
}: {
  topic: string | null;
  onTopicChange: (t: string) => void;
}) {
  const { t } = useI18n();
  const [view, setView] = useState<ViewMode>("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [customTopic, setCustomTopic] = useState("");
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [lang, setLang] = useState<InterviewLang>("en");
  const langRef = useRef<InterviewLang>(lang);
  langRef.current = lang;
  const [scene, setScene] = useState<SceneKey>("office");
  const [micMuted, setMicMuted] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const [usedQuestionIds, setUsedQuestionIds] = useState<number[]>([]);
  const nextIdRef = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const interview = useInterview();
  const mutateAsync = interview.mutateAsync;
  const isPending = interview.isPending;

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || (messages.length === 0 && !isPending)) return;
    el.scrollTo?.({ top: el.scrollHeight });
  }, [messages, isPending]);

  const addMessage = useCallback((role: "interviewer" | "user", text: string) => {
    setMessages((prev) => [...prev, { role, text, id: nextIdRef.current++ }]);
  }, []);

  const toApiHistory = useCallback(
    (): InterviewMessage[] => messages.map((m) => ({ role: m.role, content: m.text })),
    [messages],
  );

  const speakQuestion = useCallback((text: string) => {
    setSpeaking(true);
    speak(text, () => setSpeaking(false));
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setUsedQuestionIds([]);
    nextIdRef.current = 0;
  }, []);

  const start = useCallback(
    async (nextTopic: string) => {
      reset();
      try {
        const result = await mutateAsync({
          topic: nextTopic,
          lang: langRef.current,
          usedQuestionIds: [],
          messages: [],
        });
        addMessage("interviewer", result.question);
        speakQuestion(result.question);
        if (result.question_id) setUsedQuestionIds([result.question_id]);
      } catch {
        addMessage("interviewer", t("interview.error"));
      }
    },
    [mutateAsync, addMessage, t, speakQuestion, reset],
  );

  useEffect(() => {
    if (topic) void start(topic);
  }, [topic, start]);

  const appendInterviewerTurn = useCallback(
    (result: InterviewOut) => {
      if (result.feedback) {
        const banner =
          result.verdict === "ok"
            ? `✅ ${t("interview.good")}`
            : result.verdict === "needs_work"
              ? `⚠️ ${t("interview.needsWork")}`
              : null;
        const parts = [
          banner,
          result.feedback,
          result.corrected ? `💡 ${t("interview.corrected")}: ${result.corrected}` : null,
        ].filter(Boolean);
        addMessage("interviewer", parts.join("\n\n"));
      }
      if (result.question) {
        addMessage("interviewer", result.question);
        speakQuestion(result.question);
      }
    },
    [addMessage, speakQuestion, t],
  );

  const advance = useCallback(
    async (answer: string) => {
      const userMsg = answer.trim();
      if (!userMsg || isPending) return;
      addMessage("user", userMsg);
      setInput("");
      try {
        const result = await mutateAsync({
          topic: topic ?? "General",
          lang: langRef.current,
          usedQuestionIds,
          messages: [...toApiHistory(), { role: "user", content: userMsg }],
        });
        appendInterviewerTurn(result);
        if (result.question_id) {
          const qid: number = result.question_id;
          setUsedQuestionIds((prev) => (prev.includes(qid) ? prev : [...prev, qid]));
        }
      } catch {
        addMessage("interviewer", t("interview.error"));
      }
    },
    [
      mutateAsync,
      addMessage,
      t,
      toApiHistory,
      appendInterviewerTurn,
      usedQuestionIds,
      isPending,
      topic,
    ],
  );

  const requestBank = useCallback(
    async (mode: "next" | "random") => {
      if (isPending || !topic) return;
      try {
        const result = await mutateAsync({
          topic,
          lang: langRef.current,
          mode,
          usedQuestionIds,
          messages: [],
        });
        appendInterviewerTurn(result);
        if (result.question_id) {
          const qid: number = result.question_id;
          setUsedQuestionIds((prev) => (prev.includes(qid) ? prev : [...prev, qid]));
        }
      } catch {
        addMessage("interviewer", t("interview.error"));
      }
    },
    [mutateAsync, addMessage, t, appendInterviewerTurn, usedQuestionIds, isPending, topic],
  );

  const steerTopic = useCallback(async () => {
    const topicText = customTopic.trim();
    if (!topicText || isPending) return;
    setCustomTopic("");
    const phrase =
      langRef.current === "ru"
        ? `Давай поговорим про ${topicText}.`
        : `Let's talk about ${topicText}.`;
    await advance(phrase);
  }, [advance, customTopic, isPending]);

  const handleTranscript = useCallback((transcript: string) => {
    setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
  }, []);

  const handleCallAnswer = useCallback(
    (transcript: string) => {
      void advance(transcript);
    },
    [advance],
  );

  const endCall = useCallback(() => {
    reset();
    setView("chat");
  }, [reset]);

  const mascotEmotion: Emotion = speaking
    ? "speaking"
    : listening
      ? "listening"
      : isPending
        ? "thinking"
        : "idle";

  const callStatus = speaking
    ? t("interview.callSpeaking")
    : listening
      ? t("interview.callListening")
      : isPending
        ? t("interview.thinking")
        : t("interview.callReady");

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-muted-foreground">
          {t("interview.pickTopic")}
        </span>
        <div className="flex gap-1 rounded-2xl border border-border bg-card p-1">
          {TOPICS.map((item) => (
            <Button
              key={item.value}
              variant={topic === item.value ? "default" : "ghost"}
              onClick={() => onTopicChange(item.value)}
              className={
                topic === item.value
                  ? "rounded-xl font-extrabold"
                  : "rounded-xl text-muted-foreground"
              }
            >
              {t(item.labelKey)}
            </Button>
          ))}
        </div>
        <div className="ml-auto flex gap-1 rounded-2xl border border-border bg-card p-1">
          <Button
            variant={view === "chat" ? "default" : "ghost"}
            onClick={() => setView("chat")}
            className={
              view === "chat" ? "rounded-xl font-extrabold" : "rounded-xl text-muted-foreground"
            }
          >
            {t("interview.viewChat")}
          </Button>
          <Button
            variant={view === "call" ? "default" : "ghost"}
            onClick={() => setView("call")}
            className={
              view === "call" ? "rounded-xl font-extrabold" : "rounded-xl text-muted-foreground"
            }
          >
            {t("interview.viewCall")}
          </Button>
        </div>
        <div className="flex gap-1 rounded-2xl border border-border bg-card p-1">
          {LANGS.map((item) => (
            <Button
              key={item.value}
              variant={lang === item.value ? "default" : "ghost"}
              onClick={() => setLang(item.value)}
              className={
                lang === item.value
                  ? "rounded-xl font-extrabold"
                  : "rounded-xl text-muted-foreground"
              }
            >
              {t(item.labelKey)}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Mascot emotion={mascotEmotion} className="h-16 w-16" />
        <input
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              void steerTopic();
            }
          }}
          placeholder={t("interview.customTopic")}
          className="min-w-0 flex-1 rounded-xl border border-border bg-card px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
        />
        <Button onClick={() => void steerTopic()} disabled={isPending || !customTopic.trim()}>
          {t("interview.changeTopic")}
        </Button>
      </div>

      {view === "call" && (
        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="relative aspect-video w-full">
            <LocationScene scene={scene} className="absolute inset-0 h-full w-full" />
            <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/60" />

            <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/40 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
              <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
              {t("interview.callLive")}
            </div>

            <div className="absolute right-3 top-3 flex gap-1 rounded-full bg-black/40 p-1 backdrop-blur">
              {SCENES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setScene(s.value)}
                  className={
                    scene === s.value
                      ? "rounded-full bg-white/90 px-2 py-1 text-[10px] font-bold text-black"
                      : "rounded-full px-2 py-1 text-[10px] font-semibold text-white/80 hover:text-white"
                  }
                >
                  {t(s.labelKey)}
                </button>
              ))}
            </div>

            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              {cameraOn ? (
                <Mascot emotion={mascotEmotion} className="h-44 w-44 drop-shadow-xl" />
              ) : (
                <div className="flex h-32 w-32 items-center justify-center rounded-full bg-muted text-5xl font-black text-muted-foreground">
                  {t("interview.callAvatar")}
                </div>
              )}
              <span className="rounded-full bg-black/40 px-3 py-1 text-sm font-bold text-white backdrop-blur">
                {callStatus}
              </span>
              {micMuted && (
                <span className="flex items-center gap-1 rounded-full bg-red-500/80 px-2 py-0.5 text-[10px] font-bold text-white">
                  <MicOff className="h-3 w-3" />
                  {t("interview.callMuted")}
                </span>
              )}
            </div>

            <div className="absolute inset-x-0 bottom-0 px-4 pb-2">
              {topic ? (
                <div
                  ref={scrollRef}
                  className="mx-auto flex max-h-24 w-full max-w-md flex-col gap-1.5 overflow-y-auto rounded-xl bg-black/40 p-3 text-xs text-white backdrop-blur"
                >
                  {messages.length === 0 && !isPending && (
                    <span className="text-white/70">{t("interview.callWaiting")}</span>
                  )}
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      className={`max-w-[85%] whitespace-pre-line rounded-lg px-2.5 py-1 ${
                        m.role === "user" ? "ml-auto bg-primary/80" : "mr-auto bg-white/15"
                      }`}
                    >
                      {m.text}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mx-auto w-full max-w-md rounded-xl bg-black/40 p-3 text-center text-sm font-semibold text-white backdrop-blur">
                  {t("interview.chooseTopicFirst")}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-center gap-4 border-t border-border bg-card p-4">
            <button
              type="button"
              onClick={() => setMicMuted((v) => !v)}
              aria-label={t(micMuted ? "interview.callUnmute" : "interview.callMute")}
              className={`flex h-12 w-12 items-center justify-center rounded-full transition ${
                micMuted ? "bg-red-500 text-white" : "bg-muted text-foreground hover:bg-muted/70"
              }`}
            >
              {micMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
            </button>

            <button
              type="button"
              onClick={() => setCameraOn((v) => !v)}
              aria-label={t(cameraOn ? "interview.callCameraOff" : "interview.callCameraOn")}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-foreground transition hover:bg-muted/70"
            >
              {cameraOn ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
            </button>

            {topic && (
              <MicButton
                onTranscript={handleCallAnswer}
                disabled={isPending || speaking || micMuted}
                continuous
                onListeningChange={setListening}
                className="h-14 w-14 text-xl"
              />
            )}

            <button
              type="button"
              onClick={endCall}
              aria-label={t("interview.callEnd")}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-red-600 text-white transition hover:bg-red-700"
            >
              <PhoneOff className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {view === "chat" && (
        <>
          <div
            ref={scrollRef}
            className="flex max-h-96 flex-col gap-2 overflow-y-auto rounded-md bg-muted/30 p-3 text-sm"
          >
            {!topic && (
              <span className="text-sm text-muted-foreground">
                {t("interview.chooseTopicFirst")}
              </span>
            )}
            {topic && messages.length === 0 && isPending && (
              <Loader label={t("interview.thinking")} />
            )}
            {messages.map((m) => (
              <HoverableSentence key={m.id} text={m.text}>
                <div
                  className={`max-w-[85%] whitespace-pre-line rounded-lg px-3 py-2 ${
                    m.role === "user"
                      ? "ml-auto bg-primary text-primary-foreground"
                      : "mr-auto bg-background text-foreground"
                  }`}
                >
                  {m.text}
                </div>
              </HoverableSentence>
            ))}
          </div>

          {topic && (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={t("interview.placeholder")}
                  rows={2}
                  className="flex-1"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void advance(input);
                    }
                  }}
                />
                <MicButton
                  onTranscript={handleTranscript}
                  disabled={isPending}
                  continuous
                  onListeningChange={setListening}
                />
                <Button
                  onClick={() => void advance(input)}
                  disabled={isPending || !input.trim()}
                  className="self-end"
                >
                  {t("interview.send")}
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => void requestBank("next")}
                  disabled={isPending}
                >
                  {t("interview.nextQuestion")}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => void requestBank("random")}
                  disabled={isPending}
                >
                  {t("interview.randomQuestion")}
                </Button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
