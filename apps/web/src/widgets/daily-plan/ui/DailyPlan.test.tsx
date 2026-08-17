import { screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { DailyPlan } from "./DailyPlan";

const TODAY = {
  steps: [
    { kind: "review", vocab_due: 3, skill_due: 1 },
    {
      kind: "read_lesson",
      module_id: "b1.grammar.articles",
      title: "Articles",
      level: "B1",
      track: "grammar",
    },
    { kind: "produce", word: "run", card_id: 1 },
    {
      kind: "focus",
      leeches: [
        {
          id: 1,
          skill: "art.definite",
          module_id: "b1.grammar.articles",
          source_item_id: "q1",
          is_leech: true,
        },
      ],
    },
  ],
};

function renderPlan() {
  return renderWithProviders(
    <MemoryRouter>
      <DailyPlan />
    </MemoryRouter>,
  );
}

describe("DailyPlan", () => {
  it("renders every step of the today session", async () => {
    server.use(http.get("/api/session/today", () => HttpResponse.json(TODAY)));
    renderPlan();

    expect(await screen.findByText("Разминка")).toBeInTheDocument();
    expect(screen.getByText("Слова · 3")).toBeInTheDocument();
    expect(screen.getByText("Навыки · 1")).toBeInTheDocument();
    expect(await screen.findByText("Прочитай урок")).toBeInTheDocument();
    expect(screen.getByText("Articles · B1 grammar")).toBeInTheDocument();
    expect(await screen.findByText("Продукция")).toBeInTheDocument();
    expect(screen.getByText('Составь предложение со словом: "run"')).toBeInTheDocument();
    expect(await screen.findByText("Фокус")).toBeInTheDocument();
    expect(screen.getByText("art.definite")).toBeInTheDocument();
  });

  it("links the learn step to the lesson and quiz screens", async () => {
    server.use(
      http.get("/api/session/today", () =>
        HttpResponse.json({
          steps: [
            {
              kind: "take_quiz",
              module_id: "b1.grammar.articles",
              title: "Articles",
              level: "B1",
              track: "grammar",
              items: 2,
            },
          ],
        }),
      ),
    );
    renderPlan();

    const link = await screen.findByRole("link", { name: /Articles/ });
    expect(link).toHaveAttribute("href", "/learn/b1.grammar.articles/quiz");
    expect(await screen.findByText("Вопросов · 2")).toBeInTheDocument();
  });

  it("shows an empty state when nothing is due", async () => {
    server.use(http.get("/api/session/today", () => HttpResponse.json({ steps: [] })));
    renderPlan();

    expect(
      await screen.findByText("Всё выполнено — на сегодня ничего не осталось."),
    ).toBeInTheDocument();
  });
});
