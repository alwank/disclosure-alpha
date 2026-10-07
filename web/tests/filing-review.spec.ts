import { expect, test } from "@playwright/test";
import { makeReview, makeReviewWithChanges } from "./fixture";

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
  await page.getByRole("button", { name: "Next →" }).click();
  await expect(page.getByText("3 / 3")).toBeVisible();
});

test("mobile drawer filters evidence and search navigation keeps reader focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReview() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  await page.getByRole("button", { name: /details & evidence 3/i }).click();
  const drawer = page.getByRole("dialog", { name: "Review context" });
  await drawer.getByRole("combobox", { name: "Filter evidence by flag" }).selectOption("material_weakness_flag");
  await expect(drawer.getByText("2 of 3 phrases")).toBeVisible();
  await drawer.getByRole("button", { name: "Next →" }).click();
  await expect(drawer).toBeHidden();
  await expect(page.locator('[data-selected-hit="true"]')).toHaveText("material weakness");
  const searchbox = page.getByRole("searchbox", { name: "Search text" });
  await searchbox.fill("material weakness");
  await searchbox.press("Enter");
  await expect(page.getByText("1 of 2")).toBeVisible();
  await expect(searchbox).toBeFocused();
  await page.getByRole("button", { name: "Next search match" }).click();
  await expect(page.getByText("2 of 2")).toBeVisible();
  await expect(searchbox).toBeFocused();
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
  await page.getByRole("button", { name: /details & evidence 3/i }).click();
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

test("intermediate evidence drawer keeps keyboard focus and closes with Escape", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1100, height: 820 });
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReview() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  const toggle = page.getByRole("button", { name: /details & evidence 3/i });
  await toggle.click();
  const drawer = page.getByRole("dialog", { name: "Review context" });
  await expect(drawer).toBeVisible();
  await expect(
    drawer.getByRole("button", { name: "Close evidence" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(
    drawer
      .getByRole("button", { name: /material weakness: material weakness/i })
      .last(),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(toggle).toBeFocused();
});

test("section change bars open current text and signed comparison drivers", async ({
  page,
}) => {
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReviewWithChanges() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  const changes = page.getByRole("button", {
    name: /change magnitude .* out of 100/i,
  });
  await expect(changes.first()).toHaveAttribute(
    "aria-label",
    /Item 1A Risk Factors, change magnitude 72.1/,
  );
  await changes.first().click();
  await expect(page.getByText("+1.25 pp")).toBeVisible();
  await expect(page.getByText("-0.75 pp")).toBeVisible();
  await expect(
    page.getByText(/current filing text · no passage diff/i),
  ).toBeVisible();
  await expect(page.locator('[data-selected-hit="true"]')).toHaveCount(0);
  await expect(page.locator(".flag-highlight")).toHaveCount(0);
  await page.screenshot({
    path: "test-results/filing-review-changes.png",
    fullPage: true,
  });
});

test("mobile change selection opens drivers and returns to unmarked current text", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/v1/company/*/filing-review?*", async (route) => {
    await route.fulfill({ json: makeReviewWithChanges() });
  });
  await page.goto("/app/");
  await page.getByRole("button", { name: /open filing/i }).click();
  await page
    .getByRole("button", { name: /item 1a risk factors, change magnitude/i })
    .click();
  const drawer = page.getByRole("dialog", { name: "Review context" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByText("+1.25 pp")).toBeVisible();
  await page.screenshot({
    path: "test-results/filing-review-mobile-changes.png",
    fullPage: true,
  });
  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(
    page.getByText(/current filing text · no passage diff/i),
  ).toBeVisible();
  await expect(page.locator(".flag-highlight")).toHaveCount(0);
});
