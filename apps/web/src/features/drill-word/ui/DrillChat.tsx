import { useState } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/button";
import { HoverableSentence } from "@/shared/ui/hoverable-sentence";
import { Loader } from "@/shared/ui/loader";
import { MicButton } from "@/shared/ui/mic-button";
import { Textarea } from "@/shared/ui/textarea";
import { useDrillWord } from "../model/use-drill-word";

type Message = { role: "user" | "ai"; text: string };

export function DrillChat({
  cardId,
  word,
  onClose,
}: {
  cardId: number;
  word: string;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<(Message & { id: number })[]>([]);
  const [input, setInput] = useState("");
  const [nextId, setNextId] = useState(0);
  const drill = useDrillWord(cardId);

  const addMessage = (role: "user" | "ai", text: string) => {
    setMessages((prev) => [...prev, { role, text, id: nextId }]);
    setNextId((n) => n + 1);
  };

  const send = async () => {
    if (!input.trim() || drill.isPending) return;
    const userMsg = input.trim();
    setInput("");
    addMessage("user", userMsg);
    try {
      const result = await drill.mutateAsync(userMsg);
      const aiText = result.response + (result.question ? `\n\n${result.question}` : "");
      addMessage("ai", aiText);
    } catch {
      addMessage("ai", t("drill.error"));
    }
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="font-extrabold">
          {t("practice.drillTitle")}: <span className="text-primary">{word}</span>
        </span>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ✕
        </Button>
      </div>

      <div className="flex max-h-80 flex-col gap-2 overflow-y-auto rounded-xl bg-tint-lavender p-3 text-sm">
        {messages.length === 0 && (
          <p className="text-muted-foreground">
            {t("drill.greeting")} «<span className="font-extrabold">{word}</span>»,{" "}
            {t("drill.reply")}
          </p>
        )}
        {messages.map((m) => (
          <HoverableSentence key={m.id} text={m.text}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 ${
                m.role === "user"
                  ? "ml-auto bg-primary text-primary-foreground"
                  : "mr-auto bg-white text-foreground"
              }`}
            >
              {m.text}
            </div>
          </HoverableSentence>
        ))}
        {drill.isPending && <Loader />}
      </div>

      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("drill.placeholder")}
          rows={2}
          className="flex-1"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <MicButton onTranscript={setInput} disabled={drill.isPending} continuous />
        <Button onClick={send} disabled={drill.isPending || !input.trim()} className="self-end">
          {t("drill.send")}
        </Button>
      </div>
    </div>
  );
}
