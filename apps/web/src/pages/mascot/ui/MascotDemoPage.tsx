import { useState } from "react";
import { Button } from "@/shared/ui/button";
import type { Emotion } from "@/shared/ui/mascot";
import { Mascot } from "@/shared/ui/mascot";

const EMOTIONS: Emotion[] = ["idle", "happy", "sad", "thinking", "listening", "speaking"];

export function MascotDemoPage() {
  const [emotion, setEmotion] = useState<Emotion>("idle");

  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-border bg-card p-8">
      <Mascot emotion={emotion} className="h-64 w-64" />
      <div className="flex flex-wrap justify-center gap-2">
        {EMOTIONS.map((e) => (
          <Button
            key={e}
            variant={emotion === e ? "default" : "outline"}
            onClick={() => setEmotion(e)}
          >
            {e}
          </Button>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">
        Current: <span className="font-bold text-foreground">{emotion}</span>
      </p>
    </div>
  );
}
