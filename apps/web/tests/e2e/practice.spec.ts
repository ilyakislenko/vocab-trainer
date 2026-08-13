import { expect, test } from "@playwright/test";

test("practise a sentence with LLM feedback", async ({ page }) => {
  await page.goto("/practice");
  const main = page.getByRole("main");
  await expect(main.getByText(/write a sentence using/i)).toBeVisible();
  // Scope to <main>: the header also has a "New deck…" textbox, so the bare
  // role would be ambiguous.
  await main.getByRole("textbox").fill("I run every day.");
  await main.getByRole("button", { name: /check/i }).click();
  // Exact match: the feedback body text "Looks good." (with period) would
  // also match a loose /looks good/i, making the locator ambiguous.
  await expect(main.getByText("Looks good", { exact: true })).toBeVisible(); // default practice handler → verdict ok
});
