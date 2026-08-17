import { useMutation } from "@tanstack/react-query";
import { apiClient, type components, type PronunciationAssessment } from "@/shared/api";

export function recordAudio(): Promise<Blob> {
  return new Promise<Blob>((resolve, reject) => {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      reject(new Error("Recording is not supported in this browser"));
      return;
    }
    const stop = (stream: MediaStream) => {
      stream.getTracks().forEach((track) => {
        track.stop();
      });
    };

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const recorder = new MediaRecorder(stream);
        const chunks: Blob[] = [];
        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) chunks.push(event.data);
        };
        recorder.onstop = () => {
          stop(stream);
          resolve(new Blob(chunks, { type: recorder.mimeType || "audio/webm" }));
        };
        recorder.onerror = () => {
          stop(stream);
          reject(new Error("Recording failed"));
        };
        recorder.start();
        // A short fixed window: the learner taps record and speaks immediately.
        window.setTimeout(() => {
          if (recorder.state !== "inactive") recorder.stop();
        }, 5000);
      })
      .catch((error: unknown) => reject(error instanceof Error ? error : new Error(String(error))));
  });
}

export function useScorePronunciation() {
  return useMutation({
    mutationFn: async (target: string): Promise<PronunciationAssessment> => {
      const blob = await recordAudio();
      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");
      formData.append("target", target);
      const { data, error } = await apiClient.POST("/pronounce/score", {
        body: formData as unknown as components["schemas"]["Body_score_pronunciation_pronounce_score_post"],
      });
      if (error) throw new Error("Pronunciation scoring failed");
      return data;
    },
  });
}
