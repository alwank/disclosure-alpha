import { expect, test } from "@playwright/test";
import { makeReview } from "./fixture";

test("clicking a flag selects and highlights its exact filing phrase", async ({
  page,
}) => {
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReview() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  await page
    .getByRole("button", { name: /material weakness: material weakness/i })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Item 9A Controls" }),
  ).toBeVisible();
  await expect(page.locator('[data-selected-hit="true"]')).toHaveText(
    "material weakness",
  );
  await page.screenshot({
    path: "test-results/filing-review.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /next/i }).click();
  await expect(page.getByText("3 / 3")).toBeVisible();
});

test("mobile evidence selection opens the reader with the highlighted phrase", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReview() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  await page
    .getByRole("navigation", { name: "Review panels" })
    .getByRole("button", { name: "Evidence" })
    .click();
  await page
    .getByRole("button", { name: /material weakness: material weakness/i })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Item 9A Controls" }),
  ).toBeVisible();
  await expect(page.locator('[data-selected-hit="true"]')).toHaveText(
    "material weakness",
  );
  await page.screenshot({
    path: "test-results/filing-review-mobile.png",
    fullPage: true,
  });
});

test("intermediate evidence drawer keeps keyboard focus and closes with Escape", async ({ page }) => {
  await page.setViewportSize({ width: 1100, height: 820 });
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReview() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  const toggle = page.getByRole("button", { name: /evidence 3/i });
  await toggle.click();
  const drawer = page.getByRole("dialog", { name: "Flag evidence" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "Close evidence" })).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(drawer.getByRole("button", { name: /material weakness: material weakness/i }).last()).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(toggle).toBeFocused();
});
