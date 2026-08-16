/**
 * Web Audio API sound effects — no external files needed.
 */

type WindowWithWebkitAudio = Window & { webkitAudioContext?: typeof AudioContext };

const resolveAudioCtor = (): typeof AudioContext | undefined =>
  window.AudioContext ?? (window as WindowWithWebkitAudio).webkitAudioContext;

const ctx = (): AudioContext | null => {
  try {
    const Ctor = resolveAudioCtor();
    return Ctor ? new Ctor() : null;
  } catch {
    return null;
  }
};

function playTone(freq: number, duration: number, type: OscillatorType = "sine") {
  const audioCtx = ctx();
  if (!audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  osc.connect(gain).connect(audioCtx.destination);
  osc.start();
  osc.stop(audioCtx.currentTime + duration);
}

/**
 * Success chime: ascending C-E-G
 */
export function playSuccess() {
  playTone(523, 0.15); // C5
  setTimeout(() => playTone(659, 0.15), 120); // E5
  setTimeout(() => playTone(784, 0.25), 240); // G5
}

/**
 * Error buzz: low dissonant tone
 */
export function playError() {
  playTone(200, 0.3, "sawtooth");
  setTimeout(() => playTone(180, 0.35, "sawtooth"), 100);
}

/**
 * Subtle tick for navigation
 */
export function playTick() {
  playTone(800, 0.05);
}
