import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { LessonReader } from "./LessonReader";

const LESSON = {
  markdown:
    "# Dependent prepositions\n\nSome words demand a **fixed preposition**.\n\n| Verb | Prep |\n|---|---|\n| depend | on |",
  meta: {
    id: "b1.grammar.dependent-prepositions",
    title: "Dependent prepositions",
    level: "B1",
    track: "grammar",
    estimated_minutes: 8,
    objectives: ["Use the correct preposition after common verbs."],
    skills: ["prep.depend-on"],
    references: [{ book: "English Grammar in Use (Murphy)", locator: "Units 133–136" }],
  },
};

function renderLesson() {
  return renderWithProviders(
    <MemoryRouter initialEntries={["/learn/b1.grammar.dependent-prepositions"]}>
      <Routes>
        <Route
          path="/learn/:moduleId"
          element={<LessonReader moduleId="b1.grammar.dependent-prepositions" />}
        />
        <Route path="/learn" element={<p>map page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LessonReader", () => {
  it("renders the lesson markdown and metadata", async () => {
    server.use(http.get("/api/curriculum/lessons/:moduleId", () => HttpResponse.json(LESSON)));
    renderLesson();

    await waitFor(() => expect(screen.getByText("fixed preposition")).toBeInTheDocument());
    expect(screen.getAllByText("Dependent prepositions").length).toBeGreaterThan(0);
    expect(screen.getByText("Use the correct preposition after common verbs.")).toBeInTheDocument();
    expect(screen.getByText("prep.depend-on")).toBeInTheDocument();
    expect(screen.getByText(/English Grammar in Use/)).toBeInTheDocument();
  });

  it("marks the lesson read and navigates back to the map", async () => {
    server.use(
      http.get("/api/curriculum/lessons/:moduleId", () => HttpResponse.json(LESSON)),
      http.post("/api/curriculum/lessons/:moduleId/read", () =>
        HttpResponse.json({
          module_id: "b1.grammar.dependent-prepositions",
          status: "in_progress",
          lesson_read_at: "2026-08-17T08:00:00Z",
          quiz_best_score: null,
          completed_at: null,
        }),
      ),
    );
    renderLesson();

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /mark as read|отметить/i })).toBeInTheDocument(),
    );
    await userEvent.click(screen.getByRole("button", { name: /mark as read|отметить/i }));

    await waitFor(() => expect(screen.getByText("map page")).toBeInTheDocument());
  });
});
