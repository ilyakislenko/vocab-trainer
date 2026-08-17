import { renderHook } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { useRevealShortcut } from "./use-reveal-shortcut";

describe("useRevealShortcut", () => {
  it("reveals on Space and Enter when enabled", async () => {
    const onReveal = vi.fn();
    renderHook(() => useRevealShortcut(true, onReveal));

    await userEvent.keyboard(" ");
    await userEvent.keyboard("{Enter}");

    expect(onReveal).toHaveBeenCalledTimes(2);
  });

  it("does nothing when disabled", async () => {
    const onReveal = vi.fn();
    renderHook(() => useRevealShortcut(false, onReveal));

    await userEvent.keyboard(" ");

    expect(onReveal).not.toHaveBeenCalled();
  });

  it("ignores Space typed into a text field", async () => {
    const onReveal = vi.fn();
    const input = document.createElement("input");
    document.body.appendChild(input);
    renderHook(() => useRevealShortcut(true, onReveal));

    input.focus();
    await userEvent.keyboard(" ");

    expect(onReveal).not.toHaveBeenCalled();
    input.remove();
  });

  it("leaves other keys alone", async () => {
    const onReveal = vi.fn();
    renderHook(() => useRevealShortcut(true, onReveal));

    await userEvent.keyboard("a");

    expect(onReveal).not.toHaveBeenCalled();
  });
});
