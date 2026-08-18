import {
  BarChart3,
  BookOpen,
  Globe,
  GraduationCap,
  MessageSquare,
  Mic,
  Moon,
  Pencil,
  Sun,
  Upload,
  User,
} from "lucide-react";
import { useEffect, useState } from "react";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";
import { useCurriculumMap } from "@/entities/curriculum";
import { useDecks } from "@/entities/deck";
import { DeckPicker } from "@/features/select-deck";
import { ImportPage } from "@/pages/import";
import { InterviewPage } from "@/pages/interview";
import { InterviewSpeakingPage } from "@/pages/interview-speaking";
import { LearnPage } from "@/pages/learn";
import { LessonPage } from "@/pages/lesson";
import { PlacementPage } from "@/pages/placement";
import { PracticePage } from "@/pages/practice";
import { ProfilePage } from "@/pages/profile";
import { QuizPage } from "@/pages/quiz";
import { ReviewPage } from "@/pages/review";
import { ReviewSkillsPage } from "@/pages/review-skills";
import { StatsPage } from "@/pages/stats";
import { TodayPage } from "@/pages/today";
import { useI18n } from "@/shared/lib/i18n";
import { Providers } from "./providers";

const PRIMARY_NAV = [
  { to: "/", icon: BookOpen, label: "nav.review" },
  { to: "/practice", icon: Pencil, label: "nav.practice" },
  { to: "/learn", icon: GraduationCap, label: "nav.learn" },
  { to: "/profile", icon: User, label: "nav.profile" },
] as const;

const TOOLS_NAV = [
  { to: "/interview", icon: MessageSquare, label: "nav.interview" },
  { to: "/speaking", icon: Mic, label: "nav.speaking" },
  { to: "/import", icon: Upload, label: "nav.import" },
  { to: "/stats", icon: BarChart3, label: "nav.stats" },
] as const;

function Logo() {
  const { t } = useI18n();
  return (
    <div className="flex items-center gap-2.5">
      <svg
        width="28"
        height="28"
        viewBox="0 0 32 32"
        fill="none"
        className="shrink-0"
        aria-label="Elingo logo"
      >
        <path
          d="M16 4C16 4 8 10 8 18C8 22.4 11.6 26 16 26C20.4 26 24 22.4 24 18C24 10 16 4 16 4Z"
          className="fill-primary"
        />
        <path
          d="M16 14C16 14 10 18 10 23C10 25.2 12.8 27 16 27C19.2 27 22 25.2 22 23C22 18 16 14 16 14Z"
          className="fill-yellow-400"
        />
      </svg>
      <h1 className="text-[19px] font-black tracking-tight text-foreground">{t("header.title")}</h1>
    </div>
  );
}

function LevelBadge() {
  const map = useCurriculumMap();
  const level = map.data?.placement_level ?? null;
  return (
    <span className="w-fit rounded-full bg-tint-lavender px-3 py-1 text-xs font-black tracking-wide text-secondary-foreground">
      {level ?? "—"}
    </span>
  );
}

function SidebarNav({
  locale,
  setLocale,
}: {
  locale: string;
  setLocale: (l: "en" | "ru") => void;
}) {
  const { t } = useI18n();
  const location = useLocation();

  const renderLinks = (items: readonly { to: string; icon: typeof BookOpen; label: string }[]) =>
    items.map(({ to, icon: Icon, label }) => {
      const active = location.pathname === to;
      return (
        <Link
          key={to}
          to={to}
          className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-extrabold transition-all ${
            active
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <Icon className="size-4.5" strokeWidth={2.5} />
          {t(label)}
        </Link>
      );
    });

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex flex-col gap-1">{renderLinks(PRIMARY_NAV)}</div>
      <div className="flex flex-col gap-1">
        <p className="px-4 text-[11px] font-black uppercase tracking-widest text-muted-foreground/70">
          {t("nav.tools")}
        </p>
        {renderLinks(TOOLS_NAV)}
      </div>
      <button
        type="button"
        onClick={() => setLocale(locale === "en" ? "ru" : "en")}
        className="mt-1 flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-extrabold text-muted-foreground hover:bg-muted hover:text-foreground"
        title={locale === "en" ? "Switch to Russian" : "Переключить на английский"}
      >
        <Globe className="size-4.5" strokeWidth={2.5} />
        {locale.toUpperCase()}
      </button>
    </div>
  );
}

function AppShell() {
  const [deckId, setDeckId] = useState<number | null>(null);
  const decks = useDecks();
  const { t, locale, setLocale } = useI18n();
  const firstDeckId = decks.data?.[0]?.id ?? null;
  const [dark, setDark] = useState(() => {
    try {
      return localStorage.getItem("vt_dark") === "true";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    if (deckId === null && firstDeckId !== null) setDeckId(firstDeckId);
  }, [deckId, firstDeckId]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try {
      localStorage.setItem("vt_dark", String(dark));
    } catch {}
  }, [dark]);

  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col gap-6 border-r border-sidebar-border bg-sidebar px-5 py-7">
          <div className="flex flex-col gap-2">
            <Logo />
            <LevelBadge />
          </div>
          <SidebarNav locale={locale} setLocale={setLocale} />
          <div className="flex flex-col gap-3">
            <DeckPicker value={deckId} onChange={setDeckId} />
            <button
              type="button"
              onClick={() => setDark(!dark)}
              className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-extrabold text-muted-foreground hover:bg-muted hover:text-foreground"
              title={dark ? "Light mode" : "Dark mode"}
            >
              {dark ? (
                <Sun className="size-4.5" strokeWidth={2.5} />
              ) : (
                <Moon className="size-4.5" strokeWidth={2.5} />
              )}
              {dark ? t("nav.light") : t("nav.dark")}
            </button>
          </div>
        </aside>

        {/* Content */}
        <main className="flex-1 px-8 py-8">
          <Routes>
            <Route path="/" element={<ReviewPage deckId={deckId} />} />
            <Route path="/today" element={<TodayPage />} />
            <Route path="/profile" element={<ProfilePage deckId={deckId} />} />
            <Route path="/learn" element={<LearnPage />} />
            <Route path="/placement" element={<PlacementPage />} />
            <Route path="/learn/:moduleId" element={<LessonPage />} />
            <Route path="/learn/:moduleId/quiz" element={<QuizPage />} />
            <Route path="/learn/skills" element={<ReviewSkillsPage />} />
            <Route path="/practice" element={<PracticePage deckId={deckId} />} />
            <Route path="/interview" element={<InterviewPage />} />
            <Route path="/speaking" element={<InterviewSpeakingPage />} />
            <Route path="/import" element={<ImportPage deckId={deckId} />} />
            <Route path="/stats" element={<StatsPage deckId={deckId} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export function App() {
  return (
    <Providers>
      <AppShell />
    </Providers>
  );
}
