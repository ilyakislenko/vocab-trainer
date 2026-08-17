import { expect, test } from "@playwright/test";

test("все новые элементы видны", async ({ page }) => {
  await page.goto("/practice");
  const main = page.getByRole("main");

  await expect(main.getByRole("button", { name: "Изучаемые" })).toBeVisible();
  await expect(main.getByRole("button", { name: "Все слова" })).toBeVisible();
  await expect(main.getByRole("button", { name: "По теме" })).toBeVisible();
  await expect(main.getByText("run")).toBeVisible();
  await expect(main.getByRole("button", { name: "Прослушать произношение" })).toBeVisible();
  await expect(main.getByRole("button", { name: /Предложение/ })).toBeVisible();
  await expect(main.getByRole("button", { name: /Говорение/ })).toBeVisible();
  await expect(main.getByRole("button", { name: /Дрилл/ })).toBeVisible();
});
