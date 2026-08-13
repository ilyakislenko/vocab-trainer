import { HttpResponse, http } from "msw";

export const handlers = [
  http.get("/api/decks", () => HttpResponse.json([{ id: 1, name: "Sample" }])),
  http.post("/api/decks", async ({ request }) => {
    const body = (await request.json()) as { name: string };
    return HttpResponse.json({ id: 2, name: body.name });
  }),
  http.post("/api/decks/:id/import", () =>
    HttpResponse.json({ committed: false, imported: [], errors: [] }),
  ),
  http.get("/api/review/queue", () =>
    HttpResponse.json([{ id: 1, word: "run", translation: "бежать", transcription: "rʌn" }]),
  ),
  http.post("/api/review", async ({ request }) => {
    const body = (await request.json()) as { card_id: number };
    return HttpResponse.json({
      id: body.card_id,
      word: "run",
      translation: "бежать",
      transcription: null,
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
];
