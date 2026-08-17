import { useEffect } from "react";

/**
 * Keyboard-first review: Space or Enter reveals the answer, the same way
 * `RatingBar` binds number keys 1–4 to a rating. Together they let a whole
 * review run from the keyboard (flip → rate → next). The listener is inert
 * while `enabled` is false or while the user is typing in a field, so it never
 * steals input elsewhere on the page.
 */
export function useRevealShortcut(enabled: boolean, onReveal: () => void): void {
  useEffect(() => {
    if (!enabled) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key !== " " && e.key !== "Enter") return;
      const target = e.target;
      if (target instanceof HTMLElement) {
        const tag = target.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable) return;
      }
      e.preventDefault(); // Space would otherwise scroll the page.
      onReveal();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [enabled, onReveal]);
}
