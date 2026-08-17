import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { PlacementRunner } from "./PlacementRunner";

const PLACEMENT = {
  items: [
    {
      id: "pl.a2.1",
      level: "A2",
      type: "mcq",
      skill: "pl.tenses",
      prompt: "Where is Anna? — She ___ lunch at the moment.",
      options: ["has", "is having", "have"],
    },
    {
      id: "pl.a2.4",
      level: "A2",
      type: "cloze",
      skill: "pl.tenses",
      prompt: "It ___ rain. (two words)",
      options: null,
    },
    {
      id: "pl.b1.1",
      level: "B1",
      type: "mcq",
      skill: "pl.tenses",
      prompt: "I ___ never been to Japan.",
      options: ["have", "am", "was"],
    },
  ],
};

const GRADE = {
  level: "A2",
  current_module_id: "b1.grammar.articles",
  results: [
    {
      item_id: "pl.a2.1",
      level: "A2",
      skill: "pl.tenses",
      prompt: "Where is Anna? — She ___ lunch at the moment.",
      given: "1",
      correct: true,
      correct_answer: "is having",
      explanation: "Present continuous for now.",
    },
    {
      item_id: "pl.a2.4",
      level: "A2",
      skill: "pl.tenses",
      prompt: "It ___ rain. (two words)",
      given: "is going to",
      correct: true,
      correct_answer: "is going to",
      explanation: "Planned future.",
    },
    {
      item_id: "pl.b1.1",
      level: "B1",
      skill: "pl.tenses",
      prompt: "I ___ never been to Japan.",
      given: "bogus",
      correct: false,
      correct_answer: "have",
      explanation: "Present perfect with ever/never.",
    },
  ],
};

function renderRunner() {
  return renderWithProviders(
    <MemoryRouter initialEntries={["/placement"]}>
      <Routes>
        <Route path="/placement" element={<PlacementRunner />} />
        <Route path="/learn/:moduleId" element={<p>lesson page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("PlacementRunner", () => {
  it("walks through items and submits to estimate a level", async () => {
    server.use(
      http.get("/api/placement", () => HttpResponse.json(PLACEMENT)),
      http.post("/api/placement/grade", () => HttpResponse.json(GRADE)),
    );
    renderRunner();

    const firstPrompt = await screen.findByText(/Where is Anna/);
    expect(firstPrompt).toBeInTheDocument();
    expect(screen.getByText(/Level A2|Уровень A2/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /2\s*is having/ }));
    await userEvent.click(screen.getByRole("button", { name: /next|далее/i }));

    const gap = await screen.findByPlaceholderText(/fill in the gap|заполни пропуск/i);
    await userEvent.type(gap, "is going to");
    await userEvent.click(screen.getByRole("button", { name: /next|далее/i }));

    const secondMcq = await screen.findByText(/never been to Japan/);
    expect(secondMcq).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /1\s*have/ }));
    await userEvent.click(screen.getByRole("button", { name: /finish|завершить/i }));

    await waitFor(() =>
      expect(screen.getByText(/placement complete|тест завершён/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/A2/)).toBeInTheDocument();
    expect(screen.getByText(/how you answered|как ты отвечал/i)).toBeInTheDocument();
    expect(screen.getByText(/correct 2 of 3|верно 2 из 3/i)).toBeInTheDocument();
    expect(screen.getByText(/correct: is having|правильно: is having/i)).toBeInTheDocument();
    expect(screen.getByText(/missed|мимо/i)).toBeInTheDocument();
    expect(screen.getByText(/present perfect with ever\/never/i)).toBeInTheDocument();
    expect(screen.getByText(/your answer: bogus|твой ответ: bogus/i)).toBeInTheDocument();
  });

  it("disables Next until the current item is answered", async () => {
    server.use(http.get("/api/placement", () => HttpResponse.json(PLACEMENT)));
    renderRunner();

    await screen.findByText(/Where is Anna/);
    const next = screen.getByRole("button", { name: /next|далее/i });
    expect(next).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: /1\s*has/ }));
    expect(next).toBeEnabled();
  });

  it("continues to the recommended module after grading", async () => {
    server.use(
      http.get("/api/placement", () => HttpResponse.json(PLACEMENT)),
      http.post("/api/placement/grade", () => HttpResponse.json(GRADE)),
    );
    renderRunner();

    await screen.findByText(/Where is Anna/);
    await userEvent.click(screen.getByRole("button", { name: /2\s*is having/ }));
    await userEvent.click(screen.getByRole("button", { name: /next|далее/i }));

    const gap = await screen.findByPlaceholderText(/fill in the gap|заполни пропуск/i);
    await userEvent.type(gap, "is going to");
    await userEvent.click(screen.getByRole("button", { name: /next|далее/i }));

    await screen.findByText(/never been to Japan/);
    await userEvent.click(screen.getByRole("button", { name: /1\s*have/ }));
    await userEvent.click(screen.getByRole("button", { name: /finish|завершить/i }));

    const start = await screen.findByRole("button", { name: /start learning|начать учиться/i });
    await userEvent.click(start);
    expect(await screen.findByText("lesson page")).toBeInTheDocument();
  });
});
