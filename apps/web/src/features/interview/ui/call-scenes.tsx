import type { ReactNode } from "react";

type SceneKey = "office" | "cafe" | "park" | "night";

const SCENES: Record<SceneKey, { labelKey: string; scene: ReactNode }> = {
  office: {
    labelKey: "interview.callSceneOffice",
    scene: (
      <>
        <rect width="100%" height="100%" fill="url(#office-sky)" />
        <defs>
          <linearGradient id="office-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#BFD9F2" />
            <stop offset="100%" stopColor="#E8F1FA" />
          </linearGradient>
          <linearGradient id="office-floor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#C9A27E" />
            <stop offset="100%" stopColor="#A57F5D" />
          </linearGradient>
        </defs>
        <rect x="70" y="30" width="160" height="110" rx="8" fill="#FFFFFF" opacity="0.7" />
        <rect x="80" y="42" width="58" height="42" rx="3" fill="#7FB3D6" />
        <rect x="150" y="42" width="58" height="42" rx="3" fill="#7FB3D6" />
        <rect x="80" y="94" width="120" height="6" fill="#A9A9B5" opacity="0.5" />
        <rect x="0" y="140" width="100%" height="160" fill="url(#office-floor)" />
        <rect x="20" y="150" width="120" height="9" rx="4" fill="#6E4F37" />
        <rect x="20" y="159" width="9" height="70" fill="#5C4030" />
        <rect x="131" y="159" width="9" height="70" fill="#5C4030" />
        <rect x="10" y="170" width="26" height="60" rx="4" fill="#8CBF6B" />
        <rect x="36" y="186" width="22" height="14" rx="3" fill="#6FA34F" />
        <rect x="180" y="150" width="120" height="9" rx="4" fill="#6E4F37" />
        <rect x="180" y="159" width="9" height="70" fill="#5C4030" />
        <rect x="291" y="159" width="9" height="70" fill="#5C4030" />
        <rect x="196" y="168" width="30" height="64" rx="3" fill="#5B4636" />
        <rect x="200" y="160" width="22" height="10" rx="2" fill="#4A3828" />
      </>
    ),
  },
  cafe: {
    labelKey: "interview.callSceneCafe",
    scene: (
      <>
        <rect width="100%" height="100%" fill="url(#cafe-sky)" />
        <defs>
          <linearGradient id="cafe-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F7D9A8" />
            <stop offset="100%" stopColor="#FBEED6" />
          </linearGradient>
          <linearGradient id="cafe-floor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#B06A3A" />
            <stop offset="100%" stopColor="#8A4F2A" />
          </linearGradient>
        </defs>
        <circle cx="160" cy="60" r="26" fill="#FFE082" />
        <path d="M0 150 H100% V210 H0 Z" fill="url(#cafe-floor)" />
        <rect x="30" y="90" width="90" height="60" rx="6" fill="#7A4E2D" />
        <rect x="38" y="98" width="30" height="44" fill="#FFF6E8" />
        <rect x="80" y="98" width="30" height="44" fill="#FFF6E8" />
        <rect x="120" y="96" width="160" height="54" rx="8" fill="#9A6A3C" />
        <rect x="134" y="104" width="40" height="38" fill="#FFF6E8" />
        <rect x="180" y="104" width="40" height="38" fill="#FFF6E8" />
        <rect x="226" y="104" width="40" height="38" fill="#FFF6E8" />
        <circle cx="154" cy="123" r="12" fill="#B06A3A" />
        <circle cx="200" cy="123" r="12" fill="#B06A3A" />
        <circle cx="246" cy="123" r="12" fill="#B06A3A" />
        <rect x="286" y="120" width="40" height="30" rx="6" fill="#5C4030" />
        <rect x="292" y="126" width="10" height="16" fill="#FFF6E8" />
        <path d="M292 118 C292 112 300 112 300 118" stroke="#4A3828" strokeWidth="5" fill="none" />
      </>
    ),
  },
  park: {
    labelKey: "interview.callScenePark",
    scene: (
      <>
        <rect width="100%" height="100%" fill="url(#park-sky)" />
        <defs>
          <linearGradient id="park-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#A9D8F0" />
            <stop offset="100%" stopColor="#E7F6FF" />
          </linearGradient>
          <linearGradient id="park-grass" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8CCB6A" />
            <stop offset="100%" stopColor="#5DA843" />
          </linearGradient>
        </defs>
        <circle cx="150" cy="55" r="28" fill="#FFE082" />
        <path d="M0 150 Q80 120 160 150 T320 150 V210 H0 Z" fill="url(#park-grass)" />
        <path
          d="M60 150 C55 110 40 95 40 95 C55 95 60 100 60 100 C60 80 48 60 48 60 C62 60 68 66 70 74 C74 52 88 40 88 40 C92 60 84 72 78 78 C90 66 100 62 100 62 C98 78 88 84 82 88 C96 80 108 80 108 80 C100 92 88 96 80 98 L76 150 Z"
          fill="#2F7A3D"
        />
        <path
          d="M220 150 C215 110 200 95 200 95 C215 95 220 100 220 100 C220 80 208 60 208 60 C222 60 228 66 230 74 C234 52 248 40 248 40 C252 60 244 72 238 78 C250 66 260 62 260 62 C258 78 248 84 242 88 C256 80 268 80 268 80 C260 92 248 96 240 98 L236 150 Z"
          fill="#3A8C4A"
        />
        <rect x="130" y="140" width="70" height="9" rx="4" fill="#7A5233" />
        <rect x="130" y="149" width="8" height="40" fill="#5C4030" />
        <rect x="192" y="149" width="8" height="40" fill="#5C4030" />
        <path d="M120 156 C130 140 170 140 180 156 Z" fill="#3A8C4A" />
        <path d="M135 150 C150 120 165 120 175 150 Z" fill="#3A8C4A" />
      </>
    ),
  },
  night: {
    labelKey: "interview.callSceneNight",
    scene: (
      <>
        <rect width="100%" height="100%" fill="url(#night-sky)" />
        <defs>
          <linearGradient id="night-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1B2440" />
            <stop offset="100%" stopColor="#3A4A72" />
          </linearGradient>
          <linearGradient id="night-floor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#12182E" />
            <stop offset="100%" stopColor="#0A0E1E" />
          </linearGradient>
        </defs>
        <circle cx="40" cy="45" r="12" fill="#FFF9E0" />
        <circle cx="270" cy="70" r="9" fill="#FFF9E0" opacity="0.8" />
        <circle cx="300" cy="40" r="6" fill="#FFF9E0" opacity="0.6" />
        <rect x="0" y="130" width="100%" height="80" fill="url(#night-floor)" />
        <rect x="10" y="70" width="50" height="60" fill="#2A3557" />
        <rect x="16" y="80" width="14" height="14" fill="#FFD27D" />
        <rect x="36" y="80" width="14" height="14" fill="#FFD27D" />
        <rect x="70" y="90" width="56" height="40" fill="#2A3557" />
        <rect x="76" y="96" width="12" height="14" fill="#FFD27D" />
        <rect x="108" y="96" width="12" height="14" fill="#FFD27D" />
        <rect x="140" y="60" width="52" height="70" fill="#33406B" />
        <rect x="146" y="72" width="12" height="14" fill="#FFD27D" />
        <rect x="174" y="72" width="12" height="14" fill="#FFD27D" />
        <rect x="200" y="80" width="60" height="50" fill="#2A3557" />
        <rect x="206" y="86" width="12" height="14" fill="#FFD27D" />
        <rect x="240" y="86" width="12" height="14" fill="#FFD27D" />
        <rect x="270" y="96" width="50" height="34" fill="#33406B" />
        <rect x="276" y="102" width="12" height="12" fill="#FFD27D" />
      </>
    ),
  },
};

export function LocationScene({ scene, className }: { scene: SceneKey; className?: string }) {
  return (
    <svg
      viewBox="0 0 320 210"
      preserveAspectRatio="xMidYMid slice"
      className={className}
      role="img"
      aria-label={SCENES[scene].labelKey}
    >
      <title>{SCENES[scene].labelKey}</title>
      {SCENES[scene].scene}
    </svg>
  );
}

export type { SceneKey };
