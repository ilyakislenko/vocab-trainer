import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

function AppTitle() {
  return <h1>Vocab Trainer</h1>;
}

describe("smoke", () => {
  it("renders a heading", () => {
    render(<AppTitle />);
    expect(screen.getByRole("heading", { name: "Vocab Trainer" })).toBeInTheDocument();
  });
});
