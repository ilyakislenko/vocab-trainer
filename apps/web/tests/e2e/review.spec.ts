import { expect, test } from "@playwright/test";

test("shows the due card and lets you reveal the answer", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Vocab Trainer" })).toBeVisible();
  // default MSW handlers auto-select the sample deck and return one due
  // card, so the review face and its reveal control render.
  await expect(page.getByText("run")).toBeVisible();
  await expect(page.getByRole("button", { name: /show answer|показать ответ/i })).toBeVisible();
});
