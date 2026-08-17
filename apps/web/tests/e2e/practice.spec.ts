import { expect, test } from "@playwright/test";

test("practise a sentence with LLM feedback", async ({ page }) => {
  await page.goto("/practice");
  const main = page.getByRole("main");
  // Default MSW handlers auto-select the sample deck and return one due card,
  // so the sentence tab renders immediately. The app's default locale is
  // Russian, so the UI strings below are the ru translations.
  await expect(main.getByText(/Составь предложение с/i)).toBeVisible();
  await main.getByRole("textbox").fill("I run every day.");
  await main.getByRole("button", { name: /Проверить/i }).click();
  // Default practice handler → verdict ok → feedback.ok ("✓ Отлично!").
  await expect(main.getByText("✓ Отлично!")).toBeVisible();
});
