import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("renders the review page by default and navigates to import", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: /vocab trainer/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: /^import$|^импорт$/i }));
    await waitFor(() => expect(screen.getByText(/import words|импорт слов/i)).toBeInTheDocument());
  });
});
