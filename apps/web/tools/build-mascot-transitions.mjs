/**
 * Generates smooth "bridge" segments between the mascot's emotion states.
 *
 * The source Lottie (`ai-robo.json`) is one continuous 0..480 timeline sliced
 * by markers into named gestures (idle / yes / no / alert / thinking / jump).
 * The app plays those slices out of order, so jumping from the last frame of
 * one slice to the first frame of another snaps the pose. This script appends a
 * short tween ("bridge") for every ordered pair of emotions: it samples each
 * animated transform track at the end pose of A and the start pose of B and
 * writes a 15-frame ease-in-out between them, past the original timeline. It
 * also emits `ai-robo-transitions.json`, mapping `"from>to"` to the bridge's
 * [start, end] frames, which the player uses via playSegments([bridge, target]).
 *
 * Rerun after re-exporting the Lottie:  node tools/build-mascot-transitions.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ASSETS = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "shared", "assets");
const SRC = join(ASSETS, "ai-robo.json");
const TRANSITIONS = join(ASSETS, "ai-robo-transitions.json");

// Emotion -> [firstFrame, lastFrame] of its gesture, matching STATE_SEGMENTS
// in lottie-mascot.tsx (the single source of truth for what each state plays).
const EMOTION_SEG = {
  idle: [0, 29],
  listening: [31, 105],
  sad: [106, 180],
  speaking: [181, 270],
  thinking: [271, 390],
  happy: [391, 479],
};
const EMOTIONS = Object.keys(EMOTION_SEG);

const BASE = 490; // first bridge frame, safely past the original op (480)
const DUR = 15; // bridge length in frames (~250ms at 60fps)
const GAP = 1; // spacer between bridges (never played linearly)
const EASE_O = { x: 0.42, y: 0 };
const EASE_I = { x: 0.58, y: 1 };

/** Value of an animated keyframe track at integer frame `t`. */
function sampleAt(keys, t) {
  if (t <= keys[0].t) return keys[0].s;
  if (t >= keys[keys.length - 1].t) return keys[keys.length - 1].s;
  for (let j = 0; j < keys.length - 1; j++) {
    const a = keys[j];
    const b = keys[j + 1];
    if (a.t <= t && t < b.t) {
      if (a.h === 1 || t === a.t) return a.s;
      const r = (t - a.t) / (b.t - a.t);
      return a.s.map((va, i) => va + ((b.s[i] ?? va) - va) * r);
    }
  }
  return keys[keys.length - 1].s;
}

/** Pad two value vectors to equal length (z defaults to 0 for 2D positions). */
function align(vStart, vEnd) {
  const n = Math.max(vStart.length, vEnd.length);
  const pad = (v) => Array.from({ length: n }, (_, i) => v[i] ?? 0);
  return [pad(vStart), pad(vEnd)];
}

const doc = JSON.parse(readFileSync(SRC, "utf8"));

if ((doc.markers ?? []).some((m) => String(m.cm).startsWith("t:"))) {
  console.error(
    "ai-robo.json already contains bridge markers — restore the pristine export first.",
  );
  process.exit(1);
}

// Collect every animated transform track once: [layerIndex, propKey, keys].
const tracks = [];
for (let li = 0; li < doc.layers.length; li++) {
  const ks = doc.layers[li].ks ?? {};
  for (const key of ["p", "a", "s", "r", "o"]) {
    const prop = ks[key];
    if (
      prop &&
      prop.a === 1 &&
      Array.isArray(prop.k) &&
      prop.k.length &&
      typeof prop.k[0] === "object"
    ) {
      tracks.push({ li, key, keys: prop.k, name: doc.layers[li].nm });
    }
  }
}

const transitions = {};
let cursor = BASE;
const markers = doc.markers.slice();

for (const from of EMOTIONS) {
  for (const to of EMOTIONS) {
    if (from === to) continue;
    const start = cursor;
    const end = start + DUR;
    cursor = end + GAP;

    const frameA = EMOTION_SEG[from][1]; // end pose of the outgoing gesture
    const frameB = EMOTION_SEG[to][0]; // start pose of the incoming gesture

    for (const { key, keys, name } of tracks) {
      let vStart = sampleAt(keys, frameA);
      let vEnd = sampleAt(keys, frameB);
      // The "Cross" X-mark only belongs to the speaking gesture; keep it hidden
      // during every transition so its animated path never needs bridging.
      if (name === "Cross" && key === "o") {
        vStart = [0];
        vEnd = [0];
      }
      [vStart, vEnd] = align(vStart, vEnd);
      keys.push({ o: EASE_O, i: EASE_I, s: vStart, t: start });
      keys.push({ o: EASE_O, i: EASE_I, s: vEnd, t: end });
    }

    markers.push({ cm: `t:${from}>${to}`, tm: start, dr: DUR });
    transitions[`${from}>${to}`] = [start, end];
  }
}

const newOp = cursor + GAP;
doc.op = newOp;
for (const layer of doc.layers) layer.op = newOp; // extend so layers render on bridges
doc.markers = markers;

writeFileSync(SRC, JSON.stringify(doc));
writeFileSync(TRANSITIONS, `${JSON.stringify(transitions, null, 2)}\n`);

console.log(
  `Wrote ${Object.keys(transitions).length} bridges over ${tracks.length} tracks; ` +
    `timeline extended ${480} -> ${newOp}.`,
);
