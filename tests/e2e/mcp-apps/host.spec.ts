import { expect, test, type Page } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  // The fixture uses system fonts; external font availability must not gate it.
  await page.route(/https:\/\/fonts\.(googleapis|gstatic)\.com\//, (route) =>
    route.abort(),
  );
});

const openApp = async (page: Page) => {
  await page.goto(".");
  await expect(page.getByTestId("mcp-demo-shell")).toBeVisible();
  const sandbox = page.frameLocator("iframe");
  const app = sandbox.frameLocator('iframe[title="MCP App"]');
  await expect(
    app.getByRole("heading", { name: "Interactive market overview" }),
  ).toBeVisible();
  return app;
};

test("renders the original result and complete ToolResult in an isolated app", async ({
  page,
}) => {
  const app = await openApp(page);

  await expect(
    page.getByText(
      "The simulated chart is ready. The original text result is preserved.",
    ),
  ).toBeVisible();
  await expect(app.locator("#symbol")).toHaveText("OPEN");
  await expect(app.locator("#private")).toHaveText("local-only");
  await expect(app.locator("#isolation")).toHaveText("Isolated");

  if (process.env.MCP_APPS_SCREENSHOT_PATH) {
    await app.locator("body").screenshot({
      path: process.env.MCP_APPS_SCREENSHOT_PATH,
    });
  }

  // The self-contained App reports its new height after responsive reflow.
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      app
        .locator("body")
        .evaluate((element) =>
          Math.abs(element.getBoundingClientRect().height - window.innerHeight),
        ),
    )
    .toBeLessThan(1);
  await app
    .getByRole("button", { name: "Send follow-up message" })
    .scrollIntoViewIfNeeded();
  await expect(
    app.getByRole("button", { name: "Send follow-up message" }),
  ).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    390,
  );
});

test("routes declared callbacks and rejects writes after the owner changes", async ({
  page,
}) => {
  const app = await openApp(page);

  await app.getByRole("button", { name: "Refresh data" }).click();
  await expect(app.locator("#price")).toHaveText("129.05");
  await expect(page.getByTestId("host-log")).toContainText(
    "tools/call refresh_market",
  );

  await app.getByRole("button", { name: "Add to model context" }).click();
  await expect(page.getByTestId("host-log")).toContainText(
    "updateModelContext Selected OPEN",
  );
  await app.getByRole("button", { name: "Send follow-up message" }).click();
  await expect(page.getByTestId("host-log")).toContainText(
    "message Explain this movement",
  );

  await page.getByTestId("mode-switch").click();
  await app.getByRole("button", { name: "Refresh data" }).click();
  await expect(app.locator("#status")).toContainText("MCP app is read-only");
  await expect(page.getByTestId("host-log")).toContainText("Host session #1");
  await expect(page.getByTestId("host-log")).not.toContainText(
    "Host session #2",
  );
});

test("ignores a JSON-RPC call from the wrong window", async ({ page }) => {
  await openApp(page);
  await page.getByText("Boundary checks", { exact: true }).click();
  await page.getByTestId("spoof-message").click();

  await expect(page.getByTestId("host-log")).not.toContainText(
    "tools/call refresh_market",
  );
});

test("switches all supported languages without reopening the app session", async ({
  page,
}) => {
  const app = await openApp(page);
  await app.getByRole("button", { name: "Refresh data" }).click();
  const language = page.getByTestId("language-select");
  const locales = await language
    .locator("option")
    .evaluateAll((options) =>
      options.map((option) => (option as HTMLOptionElement).value),
    );
  expect(locales).toHaveLength(16);
  const englishHeading = await app.getByRole("heading").innerText();
  for (const locale of locales) {
    await language.selectOption(locale);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(app.locator("html")).toHaveAttribute("lang", locale);
    await expect(app.locator("html")).toHaveAttribute(
      "dir",
      locale === "ar" ? "rtl" : "ltr",
    );
    if (locale !== "en") {
      await expect(app.getByRole("heading")).not.toHaveText(englishHeading);
    }
    await expect(app.locator("#price")).toHaveText("129.05");
  }
  await expect(page.getByTestId("host-log")).not.toContainText(
    "Host session #2",
  );
  await language.selectOption("en");
  await app.getByRole("button", { name: "Add to model context" }).click();
  await expect(page.getByTestId("host-log")).toContainText(
    "updateModelContext Selected OPEN",
  );
});

test("starts in the requested locale and falls back to English for unknown locales", async ({
  page,
}) => {
  await page.goto(".?lang=ar");
  const app = page
    .frameLocator("iframe")
    .frameLocator('iframe[title="MCP App"]');
  await expect(app.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await page.setViewportSize({ width: 390, height: 844 });
  await app.locator("#message").scrollIntoViewIfNeeded();
  await expect(app.locator("#message")).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    390,
  );
  await page.goto(".?lang=unknown");
  await expect(page.getByTestId("language-select")).toHaveValue("en");
  await expect(app.getByRole("heading")).toHaveText(
    "Interactive market overview",
  );
});
