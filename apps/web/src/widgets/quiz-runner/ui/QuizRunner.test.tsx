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

  it("word_order builds the sentence by tapping tokens and submits the ordering", async () => {
    const quiz = {
      module_id: "a1.grammar.present-simple",
      status: "not_started",
      items: [
        {
          id: "q1",
          type: "word_order",
          skill: "pres.he-she-it",
          prompt: "Arrange the words into a correct sentence.",
          options: null,
          tokens: ["She", "watches", "TV", "every", "evening"],
        },
      ],
    };
    let graded: unknown;
    server.use(
      http.get("/api/curriculum/modules/:moduleId/quiz", () => HttpResponse.json(quiz)),
      http.post("/api/curriculum/quiz/grade", async ({ request }) => {
        graded = await request.json();
        return HttpResponse.json({
          module_id: "a1.grammar.present-simple",
          score: 100,
          status: "completed",
          completed: true,
          next_module_id: null,
          items: [
            {
              item_id: "q1",
              skill: "pres.he-she-it",
              correct: true,
              explanation: "Correct word order.",
              prompt: "Arrange the words into a correct sentence.",
              needs_llm: false,
            },
          ],
        });
      }),
    );
    renderQuiz();

    await screen.findByText("Arrange the words into a correct sentence.");
    for (const token of ["She", "watches", "TV", "every", "evening"]) {
      await userEvent.click(screen.getByRole("button", { name: token }));
    }

    await userEvent.click(screen.getByRole("button", { name: /check answers|проверить/i }));
    await waitFor(() =>
      expect(screen.getByText(/Score: 100%|Результат: 100%/)).toBeInTheDocument(),
    );

    const answers = (graded as { answers: { item_id: string; given: string }[] }).answers;
    expect(answers[0].given).toBe("She watches TV every evening");
  });

  it("listening hides the prompt until results and plays audio", async () => {
    const quiz = {
      module_id: "a1.grammar.present-simple",
      status: "not_started",
      items: [
        {
          id: "q9",
          type: "listening",
          skill: "pres.he-she-it",
          prompt: "He walks to work every morning.",
          options: null,
        },
      ],
    };
    server.use(
      http.get("/api/curriculum/modules/:moduleId/quiz", () => HttpResponse.json(quiz)),
      http.post("/api/curriculum/quiz/grade", () =>
        HttpResponse.json({
          module_id: "a1.grammar.present-simple",
          score: 0,
          status: "completed",
          completed: true,
          next_module_id: null,
          items: [
            {
              item_id: "q9",
              skill: "pres.he-she-it",
              correct: false,
              explanation: "You heard: He walks to work every morning.",
              prompt: "He walks to work every morning.",
              needs_llm: false,
            },
          ],
        }),
      ),
    );
    renderQuiz();

    await screen.findByRole("button", { name: /play audio|воспроизвести/i });
    expect(screen.queryByText("He walks to work every morning.")).not.toBeInTheDocument();

    await userEvent.type(screen.getByRole("textbox"), "wrong guess");
    await userEvent.click(screen.getByRole("button", { name: /check answers|проверить/i }));

    await waitFor(() =>
      expect(screen.getByText("He walks to work every morning.")).toBeInTheDocument(),
    );
  });
});
