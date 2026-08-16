import { Mic, MicOff, PhoneOff, Video, VideoOff } from "lucide-react";
import { useCallback, useRef, useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { HoverableSentence } from "@/shared/ui/hoverable-sentence";
import { Loader } from "@/shared/ui/loader";
import { type Emotion, Mascot } from "@/shared/ui/mascot";
import { MicButton } from "@/shared/ui/mic-button";
import { Textarea } from "@/shared/ui/textarea";
import { type SceneKey, useInterviewSession } from "../model/use-interview-session";
import { type SceneKey as CallSceneKey, LocationScene } from "./call-scenes";
import { FeedbackCard } from "./FeedbackCard";
import { InterviewSetup } from "./InterviewSetup";
import { InterviewSummary } from "./InterviewSummary";
import { SessionHeader } from "./SessionHeader";

type ViewMode = "chat" | "call";

const SCENES: { value: CallSceneKey; labelKey: string }[] = [
  { value: "office", labelKey: "interview.callSceneOffice" },
  { value: "cafe", labelKey: "interview.callSceneCafe" },
  { value: "park", labelKey: "interview.callScenePark" },
  { value: "night", labelKey: "interview.callSceneNight" },
];

export function InterviewChat() {
  const { t } = useI18n();
  const {
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
  } = useInterviewSession();

  const [input, setInput] = useState("");
  const [customTopic, setCustomTopic] = useState("");
  const [listening, setListening] = useState(false);
  const [micMuted, setMicMuted] = useState(false);
  const [cameraOn, setCameraOn] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const view: ViewMode = config.view;

  const setView = useCallback((next: ViewMode) => updateConfig({ view: next }), [updateConfig]);

  const handleTranscript = useCallback((transcript: string) => {
    setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
  }, []);

  const handleCallAnswer = useCallback(
    (transcript: string) => {
      void advance(transcript);
    },
    [advance],
  );

  const handleEnd = useCallback(() => {
    setMicMuted(false);
    setCameraOn(true);
    end();
  }, [end]);

  const handleRestart = useCallback(() => {
    setInput("");
    setMicMuted(false);
    setCameraOn(true);
    backToSetup();
  }, [backToSetup]);

  const handleSceneChange = useCallback(
    (scene: SceneKey) => updateConfig({ scene }),
    [updateConfig],
  );

  const mascotEmotion: Emotion = speaking
    ? "speaking"
    : listening
      ? "listening"
      : isPending
        ? "thinking"
        : reaction
          ? reaction
          : "idle";

  const callStatus = speaking
    ? t("interview.callSpeaking")
    : listening
      ? t("interview.callListening")
      : isPending
        ? t("interview.thinking")
        : t("interview.callReady");

  if (phase === "setup") {
    return (
      <InterviewSetup
        config={config}
        onConfigChange={updateConfig}
        onStart={() => void start(config)}
        isStarting={isPending}
      />
    );
  }

  if (phase === "summary") {
    return (
      <InterviewSummary
        stats={stats}
        elapsed={elapsed}
        onRestart={() => void start(config)}
        onBack={handleRestart}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <SessionHeader
        topic={config.topic}
        stats={stats}
        elapsed={elapsed}
        onEnd={handleEnd}
        onRestart={handleRestart}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Mascot emotion={mascotEmotion} className="h-16 w-16" />
        <input
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              steerTopic(customTopic);
              setCustomTopic("");
            }
          }}
          placeholder={t("interview.customTopic")}
          className="min-w-0 flex-1 rounded-xl border border-border bg-card px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
        />
        <Button
          onClick={() => {
            steerTopic(customTopic);
            setCustomTopic("");
          }}
          disabled={isPending || !customTopic.trim()}
        >
          {t("interview.changeTopic")}
        </Button>
      </div>

      <div className="flex gap-1 self-start rounded-2xl border border-border bg-card p-1">
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

      {view === "call" && (
        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="relative aspect-video w-full">
            <LocationScene scene={config.scene} className="absolute inset-0 h-full w-full" />
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
                  onClick={() => handleSceneChange(s.value)}
                  className={
                    config.scene === s.value
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
              <div
                ref={scrollRef}
                className="mx-auto flex max-h-24 w-full max-w-md flex-col gap-1.5 overflow-y-auto rounded-xl bg-black/40 p-3 text-xs text-white backdrop-blur"
              >
                {messages.length === 0 && !isPending && (
                  <span className="text-white/70">{t("interview.callWaiting")}</span>
                )}
                {messages.map((m) =>
                  m.kind === "feedback" ? (
                    <div key={m.id} className="max-w-[85%] rounded-lg bg-white/15 px-2.5 py-1">
                      {m.text}
                    </div>
                  ) : (
                    <div
                      key={m.id}
                      className={`max-w-[85%] whitespace-pre-line rounded-lg px-2.5 py-1 ${
                        m.role === "user" ? "ml-auto bg-primary/80" : "mr-auto bg-white/15"
                      }`}
                    >
                      {m.text}
                    </div>
                  ),
                )}
              </div>
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

            <MicButton
              onTranscript={handleCallAnswer}
              disabled={isPending || speaking || micMuted}
              continuous
              onListeningChange={setListening}
              className="h-14 w-14 text-xl"
            />

            <button
              type="button"
              onClick={handleEnd}
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
            className="flex max-h-96 flex-col gap-2 overflow-y-auto rounded-xl border border-border bg-card/60 p-3 text-sm"
          >
            {messages.length === 0 && isPending && <Loader label={t("interview.thinking")} />}
            {messages.map((m) => {
              if (m.kind === "feedback") {
                return (
                  <FeedbackCard
                    key={m.id}
                    verdict={m.verdict ?? null}
                    feedback={m.text}
                    corrected={m.corrected}
                  />
                );
              }
              return (
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
              );
            })}
            {isPending && <Loader label={t("interview.thinking")} className="mx-auto" />}
          </div>

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
                  setInput("");
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
              onClick={() => {
                void advance(input);
                setInput("");
              }}
              disabled={isPending || !input.trim()}
              className="self-end"
            >
              {t("interview.send")}
            </Button>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => void requestBank("next")} disabled={isPending}>
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
    </div>
  );
}
