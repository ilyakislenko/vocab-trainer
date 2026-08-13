import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RatingBar } from "./RatingBar";

describe("RatingBar", () => {
  it("calls onRate from a button click", async () => {
    const onRate = vi.fn();
    render(<RatingBar onRate={onRate} disabled={false} />);
    await userEvent.click(screen.getByRole("button", { name: /good/i }));
    expect(onRate).toHaveBeenCalledWith(3);
  });

  it("calls onRate from a number key", async () => {
    const onRate = vi.fn();
    render(<RatingBar onRate={onRate} disabled={false} />);
    await userEvent.keyboard("4");
    expect(onRate).toHaveBeenCalledWith(4);
  });

  it("ignores keys when disabled", async () => {
    const onRate = vi.fn();
    render(<RatingBar onRate={onRate} disabled={true} />);
    await userEvent.keyboard("1");
    expect(onRate).not.toHaveBeenCalled();
  });

  it("does not rate when a number is typed into a focused text input", async () => {
    const onRate = vi.fn();
    render(
      <>
        <input aria-label="deck name" />
        <RatingBar onRate={onRate} disabled={false} />
      </>,
    );
    await userEvent.type(screen.getByRole("textbox", { name: /deck name/i }), "1");
    expect(onRate).not.toHaveBeenCalled();
  });
});
