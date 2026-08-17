import { HttpResponse, http } from "msw";

const CARD = { id: 1, word: "run", translation: "бежать", transcription: "rʌn", section: "main" };

export const handlers = [
  http.get("/api/decks", () => HttpResponse.json([{ id: 1, name: "Sample" }])),
  http.post("/api/decks", async ({ request }) => {
    const body = (await request.json()) as { name: string };
    return HttpResponse.json({ id: 2, name: body.name });
  }),
  http.post("/api/decks/:id/import", () =>
    HttpResponse.json({ committed: false, imported: [], errors: [] }),
  ),
  http.get("/api/decks/:id/cards", () => HttpResponse.json([CARD])),
  http.get("/api/review/queue", () => HttpResponse.json([CARD])),
  http.get("/api/review/summary", () => HttpResponse.json({ next_due: null, reviewed_today: 0 })),
  http.post("/api/review", async ({ request }) => {
    const body = (await request.json()) as { card_id: number };
    return HttpResponse.json({
      id: body.card_id,
      word: "run",
      translation: "бежать",
      transcription: null,
      section: null,
    });
  }),
  http.get("/api/stats", () => HttpResponse.json({ due_today: 0, total_reviews: 0 })),
  http.post("/api/practice/check", () =>
    HttpResponse.json({
      verdict: "ok",
      feedback: "Looks good.",
      corrected: null,
      example: "I run daily.",
    }),
  ),
  http.get("/api/practice/example", () =>
    HttpResponse.json({ example: "She runs every morning." }),
  ),
  http.get("/api/practice/topic", () => HttpResponse.json([CARD])),
  http.get("/api/practice/hint", () =>
    HttpResponse.json({
      meaning: "Бежать — быстро передвигаться ногами.",
      example: "I run every morning.",
    }),
  ),
  http.post("/api/practice/interview", () =>
    HttpResponse.json({
      verdict: "needs_work",
      feedback: "Отвечай полнее.",
      corrected: "A component is a reusable piece of UI.",
      question: "What are props?",
      question_id: 1,
    }),
  ),
  http.post("/api/practice/drill", () =>
    HttpResponse.json({ response: "Good sentence!", question: "Now try another." }),
  ),
];
