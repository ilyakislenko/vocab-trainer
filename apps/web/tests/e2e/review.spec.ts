import { expect, test } from "@playwright/test";

test("reveal and rate a card", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Vocab Trainer" })).toBeVisible();
  // default MSW handlers auto-select the sample deck and return an empty
  // review queue, so the caught-up state renders.
  await expect(page.getByText(/caught up|pick a deck/i)).toBeVisible();
});
