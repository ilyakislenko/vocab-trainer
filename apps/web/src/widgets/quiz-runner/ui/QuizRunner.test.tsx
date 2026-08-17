import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { QuizRunner } from "./QuizRunner";

const QUIZ = {
  module_id: "b1.grammar.articles",
  status: "not_started",
  items: [
    {
      id: "b1.grammar.articles.q1",
      type: "mcq",
      skill: "art.indefinite",
      prompt: "I need ___ new laptop.",
      options: ["a", "an", "the"],
    },
    {
      id: "b1.grammar.articles.q2",
      type: "cloze",
      skill: "art.definite",
      prompt: "She plays ___ violin.",
      options: null,
    },
    {
      id: "b1.grammar.articles.q3",
      type: "error_correction",
      skill: "art.zero",
      prompt: 'Correct: "I go to the work every day."',
      options: null,
    },
  ],
};

const GRADE = {
  module_id: "b1.grammar.articles",
  score: 66.66666666666667,
  status: "completed",
  completed: true,
  next_module_id: "b1.grammar.perfect-aspect",
  items: [
    {
      item_id: "b1.grammar.articles.q1",
      skill: "art.indefinite",
      correct: true,
      explanation: "First mention of a countable noun — 'a'.",
      needs_llm: false,
    },
    {
      item_id: "b1.grammar.articles.q2",
      skill: "art.definite",
      correct: true,
      explanation: "Musical instruments take 'the'.",
      needs_llm: false,
    },
    {
      item_id: "b1.grammar.articles.q3",
      skill: "art.zero",
      correct: false,
      explanation: "'Work' here is a general activity — zero article.",
      needs_llm: false,
    },
  ],
};

function renderQuiz() {
  return renderWithProviders(
    <MemoryRouter initialEntries={["/learn/b1.grammar.articles/quiz"]}>
      <Routes>
        <Route
          path="/learn/:moduleId/quiz"
          element={<QuizRunner moduleId="b1.grammar.articles" />}
        />
        <Route path="/learn" element={<p>map page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("QuizRunner", () => {
  it("renders all quiz item types", async () => {
    server.use(http.get("/api/curriculum/modules/:moduleId/quiz", () => HttpResponse.json(QUIZ)));
    renderQuiz();

    await waitFor(() => expect(screen.getByText("I need ___ new laptop.")).toBeInTheDocument());
    expect(screen.getByText("She plays ___ violin.")).toBeInTheDocument();
    expect(screen.getByText(/Correct:/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /1\s*a/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /2\s*an/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /3\s*the/ })).toBeInTheDocument();
  });

  it("number keys select an mcq option and submit shows per-item results", async () => {
    server.use(
      http.get("/api/curriculum/modules/:moduleId/quiz", () => HttpResponse.json(QUIZ)),
      http.post("/api/curriculum/quiz/grade", () => HttpResponse.json(GRADE)),
    );
    renderQuiz();

    const firstOption = await screen.findByRole("button", { name: /1\s*a/ });
    firstOption.focus();
    await userEvent.keyboard("1");
    expect(firstOption).toHaveAttribute("aria-pressed", "true");

    const [cloze, correction] = screen.getAllByRole("textbox");
    await userEvent.type(cloze, "the");
    await userEvent.type(correction, "I go to work every day");

    await userEvent.click(screen.getByRole("button", { name: /check answers|проверить/i }));

    await waitFor(() => expect(screen.getByText(/Score: 67%|Результат: 67%/)).toBeInTheDocument());
    expect(screen.getByText(/First mention/)).toBeInTheDocument();
    expect(screen.getByText(/Musical instruments/)).toBeInTheDocument();
    expect(screen.getByText(/Модуль завершён|Module completed/)).toBeInTheDocument();
  });
});
