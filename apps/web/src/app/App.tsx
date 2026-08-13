import { useEffect, useState } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { useDecks } from "@/entities/deck";
import { DeckPicker } from "@/features/select-deck";
import { ImportPage } from "@/pages/import";
import { PracticePage } from "@/pages/practice";
import { ReviewPage } from "@/pages/review";
import { StatsPage } from "@/pages/stats";
import { Providers } from "./providers";

// Rendered inside Providers so it can read the deck list via react-query.
function AppShell() {
  const [deckId, setDeckId] = useState<number | null>(null);
  const decks = useDecks();
  const firstDeckId = decks.data?.[0]?.id ?? null;

  // Default to the first available deck once the list loads, so the app is
  // usable without an explicit selection step; the user can still switch
  // decks (or create a new one) via the DeckPicker.
  useEffect(() => {
    if (deckId === null && firstDeckId !== null) setDeckId(firstDeckId);
  }, [deckId, firstDeckId]);

  return (
    <BrowserRouter>
      <header className="flex flex-wrap items-center justify-between gap-4 border-b p-4">
        <h1 className="text-xl font-bold">Vocab Trainer</h1>
        <nav className="flex gap-4">
          <Link to="/">Review</Link>
          <Link to="/practice">Practice</Link>
          <Link to="/import">Import</Link>
          <Link to="/stats">Stats</Link>
        </nav>
        <DeckPicker value={deckId} onChange={setDeckId} />
      </header>
      <main className="p-6">
        <Routes>
          <Route path="/" element={<ReviewPage deckId={deckId} />} />
          <Route path="/practice" element={<PracticePage deckId={deckId} />} />
          <Route path="/import" element={<ImportPage deckId={deckId} />} />
          <Route path="/stats" element={<StatsPage deckId={deckId} />} />
        </Routes>
      </main>
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
