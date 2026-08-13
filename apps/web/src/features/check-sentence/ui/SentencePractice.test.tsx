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
    await userEvent.click(screen.getByRole("button", { name: /check/i }));
    await waitFor(() => expect(screen.getByText(/wrong tense/i)).toBeInTheDocument());
    expect(screen.getByText(/I ran\./)).toBeInTheDocument();
  });

  it("shows a provider-error alert on failure", async () => {
    server.use(
      http.post("/api/practice/check", () =>
        HttpResponse.json({ detail: "unavailable" }, { status: 502 }),
      ),
    );
    renderWithProviders(<SentencePractice cardId={1} word="run" />);
    await userEvent.type(screen.getByRole("textbox"), "I run.");
    await userEvent.click(screen.getByRole("button", { name: /check/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });

  it("shows an alert when fetching an example fails", async () => {
    server.use(
      http.get("/api/practice/example", () =>
        HttpResponse.json({ detail: "unavailable" }, { status: 502 }),
      ),
    );
    renderWithProviders(<SentencePractice cardId={1} word="run" />);
    await userEvent.click(screen.getByRole("button", { name: /get an example/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByText(/couldn't fetch an example/i)).toBeInTheDocument();
  });
});
