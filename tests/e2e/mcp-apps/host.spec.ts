import { expect, test, type Page } from "@playwright/test";

const openApp = async (page: Page) => {
  await page.goto(".");
  await expect(page.getByTestId("mcp-demo-shell")).toBeVisible();
  const sandbox = page.frameLocator('iframe[title="交互式结果"]');
  const app = sandbox.frameLocator('iframe[title="MCP App"]');
  await expect(
    app.getByRole("heading", { name: "本地交互式行情" }),
  ).toBeVisible();
  return app;
};

test("renders the original result and complete ToolResult in an isolated app", async ({
  page,
}) => {
  const app = await openApp(page);

  await expect(
    page.getByText("模拟图表已准备好，原始文本结果仍然保留。"),
  ).toBeVisible();
  await expect(app.locator("#symbol")).toHaveText("OPEN");
  await expect(app.locator("#private")).toHaveText("local-only");
  await expect(app.locator("#isolation")).toHaveText("已隔离");

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
    .getByRole("button", { name: "发送后续消息" })
    .scrollIntoViewIfNeeded();
  await expect(
    app.getByRole("button", { name: "发送后续消息" }),
  ).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(
    390,
  );
});

test("routes declared callbacks and rejects writes after the owner changes", async ({
  page,
}) => {
  const app = await openApp(page);

  await app.getByRole("button", { name: "刷新数据" }).click();
  await expect(app.locator("#price")).toHaveText("129.05");
  await expect(page.getByTestId("host-log")).toContainText(
    "tools/call refresh_market",
  );

  await app.getByRole("button", { name: "加入模型上下文" }).click();
  await expect(page.getByTestId("host-log")).toContainText(
    "updateModelContext Selected OPEN",
  );
  await app.getByRole("button", { name: "发送后续消息" }).click();
  await expect(page.getByTestId("host-log")).toContainText(
    "message Explain this movement",
  );

  await page.getByTestId("mode-switch").click();
  await app.getByRole("button", { name: "刷新数据" }).click();
  await expect(app.locator("#status")).toContainText("MCP app is read-only");
  await expect(page.getByTestId("host-log")).toContainText("Host session #1");
  await expect(page.getByTestId("host-log")).not.toContainText(
    "Host session #2",
  );
});

test("ignores a JSON-RPC call from the wrong window", async ({ page }) => {
  await openApp(page);
  await page.getByText("边界检查", { exact: true }).click();
  await page.getByTestId("spoof-message").click();

  await expect(page.getByTestId("host-log")).not.toContainText(
    "tools/call refresh_market",
  );
});
