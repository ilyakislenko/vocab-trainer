import { useMemo, useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import type { InterviewDifficulty, InterviewLang } from "../model/use-interview";
import {
  INTERVIEW_TOPICS,
  type InterviewView,
  QUESTION_COUNTS,
  SCENES,
  type SceneKey,
  type SessionConfig,
} from "../model/use-interview-session";

type Option<T> = { value: T; label: string };

export function InterviewSetup({
  config,
  onConfigChange,
  onStart,
  isStarting,
}: {
  config: SessionConfig;
  onConfigChange: (patch: Partial<SessionConfig>) => void;
  onStart: () => void;
  isStarting: boolean;
}) {
  const { t } = useI18n();
  const [customTopic, setCustomTopic] = useState("");

  const difficultyOptions: Option<InterviewDifficulty>[] = useMemo(
    () => [
      { value: "junior", label: t("interview.difficultyJunior") },
      { value: "middle", label: t("interview.difficultyMiddle") },
      { value: "senior", label: t("interview.difficultySenior") },
    ],
    [t],
  );

  const viewOptions: Option<InterviewView>[] = useMemo(
    () => [
      { value: "chat", label: t("interview.viewChat") },
      { value: "call", label: t("interview.viewCall") },
    ],
    [t],
  );

  const langOptions: Option<InterviewLang>[] = useMemo(
    () => [
      { value: "en", label: t("interview.langEn") },
      { value: "ru", label: t("interview.langRu") },
    ],
    [t],
  );

  const sceneOptions: Option<SceneKey>[] = useMemo(
    () =>
      SCENES.map((scene) => ({
        value: scene,
        label: t(`interview.callScene${scene[0].toUpperCase()}${scene.slice(1)}`),
      })),
    [t],
  );

  const countOptions: Option<number>[] = useMemo(
    () =>
      QUESTION_COUNTS.map((count) => ({
        value: count,
        label:
          count === 0
            ? t("interview.countUnlimited")
            : t("interview.countQuestions").replace("{n}", String(count)),
      })),
    [t],
  );

  const pickTopic = (topic: string) => {
    onConfigChange({ topic });
    setCustomTopic("");
  };

  return (
    <div className="flex flex-col gap-6 rounded-2xl border border-border bg-card p-6">
      <div>
        <span className="text-xs font-black uppercase tracking-widest text-primary">
          {t("interview.title")}
        </span>
        <h3 className="mt-1 text-xl font-black tracking-tight">{t("interview.setupTitle")}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{t("interview.setupSubtitle")}</p>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-sm font-semibold text-muted-foreground">
          {t("interview.pickTopic")}
        </span>
        <div className="flex flex-wrap gap-2">
          {INTERVIEW_TOPICS.map((topic) => (
            <Button
              key={topic}
              variant={config.topic === topic ? "default" : "outline"}
              size="sm"
              onClick={() => pickTopic(topic)}
            >
              {t(`interview.topic${topic}`)}
            </Button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={customTopic}
            onChange={(e) => setCustomTopic(e.target.value)}
            placeholder={t("interview.customTopic")}
            className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
          />
          <Button
            variant="secondary"
            onClick={() => customTopic.trim() && pickTopic(customTopic.trim())}
            disabled={!customTopic.trim()}
          >
            {t("interview.useTopic")}
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-sm font-semibold text-muted-foreground">
          {t("interview.difficulty")}
        </span>
        <div className="flex flex-wrap gap-2">
          {difficultyOptions.map((option) => (
            <Button
              key={option.value}
              variant={config.difficulty === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => onConfigChange({ difficulty: option.value })}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-sm font-semibold text-muted-foreground">
          {t("interview.questionCount")}
        </span>
        <div className="flex flex-wrap gap-2">
          {countOptions.map((option) => (
            <Button
              key={option.value}
              variant={config.questionCount === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => onConfigChange({ questionCount: option.value })}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-sm font-semibold text-muted-foreground">{t("interview.view")}</span>
        <div className="flex flex-wrap gap-2">
          {viewOptions.map((option) => (
            <Button
              key={option.value}
              variant={config.view === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => onConfigChange({ view: option.value })}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-sm font-semibold text-muted-foreground">
          {t("interview.language")}
        </span>
        <div className="flex flex-wrap gap-2">
          {langOptions.map((option) => (
            <Button
              key={option.value}
              variant={config.lang === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => onConfigChange({ lang: option.value })}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      {config.view === "call" && (
        <div className="flex flex-col gap-2">
          <span className="text-sm font-semibold text-muted-foreground">
            {t("interview.scene")}
          </span>
          <div className="flex flex-wrap gap-2">
            {sceneOptions.map((option) => (
              <Button
                key={option.value}
                variant={config.scene === option.value ? "default" : "outline"}
                size="sm"
                onClick={() => onConfigChange({ scene: option.value })}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>
      )}

      <Button onClick={onStart} disabled={isStarting} size="lg" className="self-start px-6">
        {t("interview.start")}
      </Button>
    </div>
  );
}
