import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { SentencePractice } from "./SentencePractice";

describe("SentencePractice", () => {
  it("checks a sentence and shows feedback", async () => {
    server.use(
      http.post("/api/practice/check", () =>
        HttpResponse.json({
          verdict: "needs_work",
          feedback: "Wrong tense.",
          corrected: "I ran.",
          example: "I run daily.",
        }),
      ),
    );
    renderWithProviders(<SentencePractice cardId={1} word="run" />);
    await userEvent.type(screen.getByRole("textbox"), "I runned.");
    await userEvent.click(screen.getByRole("button", { name: /check|проверить/i }));
    await waitFor(() => expect(screen.getByText(/wrong tense/i)).toBeInTheDocument());
    expect(screen.getByText(/I ran\./)).toBeInTheDocument();
  });

  it("shows a loader while the check is pending", async () => {
    server.use(http.post("/api/practice/check", () => new Promise(() => {})));
    renderWithProviders(<SentencePractice cardId={1} word="run" />);
    await userEvent.type(screen.getByRole("textbox"), "I run.");
    await userEvent.click(screen.getByRole("button", { name: /check|проверить/i }));
    await waitFor(() => expect(screen.getByText(/just a moment/i)).toBeInTheDocument());
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
