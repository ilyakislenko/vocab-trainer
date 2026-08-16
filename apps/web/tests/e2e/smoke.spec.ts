import { expect, test } from "@playwright/test";

test("все новые элементы видны", async ({ page }) => {
  await page.goto("/practice");
  const main = page.getByRole("main");

  await expect(main.locator(".text-3xl").first()).toBeVisible();
  await expect(main.locator("p.text-lg").first()).toBeVisible();
  await expect(main.getByRole("img").first()).toBeVisible();
  await expect(main.getByText("Как использовать")).toBeVisible();
  await expect(main.getByText(/← Back/)).toBeVisible();
  await expect(main.getByText(/Continue/)).toBeVisible();
  await expect(main.getByText("🔊")).toBeVisible();
});
