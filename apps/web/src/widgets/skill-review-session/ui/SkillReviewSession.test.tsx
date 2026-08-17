import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { SkillReviewSession } from "./SkillReviewSession";

const ITEM = {
  id: 1,
  skill: "art.indefinite",
  module_id: "b1.grammar.articles",
  source_item_id: "b1.grammar.articles.q1",
  is_leech: false,
  type: "mcq",
  prompt: "I need ___ new laptop.",
  options: ["a", "an", "the"],
  answers: ["a"],
  explanation: "First mention of a countable noun — 'a'.",
};

function mockQueue(items: unknown[] = [ITEM]) {
  server.use(
    http.get("/api/review/skills/queue", () => HttpResponse.json(items)),
    http.post("/api/review/skills", () =>
      HttpResponse.json({
        id: 1,
        skill: "art.indefinite",
        module_id: "b1.grammar.articles",
        source_item_id: "b1.grammar.articles.q1",
        is_leech: false,
      }),
    ),
  );
}

describe("SkillReviewSession", () => {
  it("renders the due skill item with its prompt and options", async () => {
    mockQueue();
    renderWithProviders(<SkillReviewSession />);

    expect(await screen.findByText("I need ___ new laptop.")).toBeInTheDocument();
    expect(screen.getByText("art.indefinite")).toBeInTheDocument();
    expect(screen.getByText("a")).toBeInTheDocument();
    expect(screen.getByText("an")).toBeInTheDocument();
    expect(screen.getByText("the")).toBeInTheDocument();
  });

  it("reveals the answer and explanation, then rating completes the session", async () => {
    mockQueue();
    renderWithProviders(<SkillReviewSession />);

    await userEvent.click(
      await screen.findByRole("button", { name: /Показать ответ|Show answer/i }),
    );

    expect(screen.getAllByText("a").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/First mention of a countable noun/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /Хорошо|Good/ }));

    await waitFor(() =>
      expect(screen.getByText(/Сессия завершена|Session complete/)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Навыков повторено|Skill items reviewed/)).toBeInTheDocument();
  });

  it("reveals the answer with the Space key (keyboard-first)", async () => {
    mockQueue();
    renderWithProviders(<SkillReviewSession />);

    // Flip the card from the keyboard instead of clicking "Show answer".
    expect(await screen.findByText("I need ___ new laptop.")).toBeInTheDocument();
    await userEvent.keyboard(" ");

    expect(screen.getByText(/First mention of a countable noun/)).toBeInTheDocument();
  });

  it("shows the caught-up state when the queue is empty", async () => {
    mockQueue([]);
    renderWithProviders(<SkillReviewSession />);

    expect(await screen.findByText(/Всё повторено|You're all caught up/)).toBeInTheDocument();
  });
});
