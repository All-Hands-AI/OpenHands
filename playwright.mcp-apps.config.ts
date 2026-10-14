import { defineConfig } from "@playwright/test";

const executablePath = process.env.MCP_APPS_BROWSER_PATH;

export default defineConfig({
  testDir: "./tests/e2e/mcp-apps",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3101/src/fixtures/mcp-apps/",
    trace: "retain-on-failure",
    launchOptions: executablePath ? { executablePath } : {},
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: {
    command: "node scripts/mcp-app-demo.mjs",
    url: "http://127.0.0.1:3101/src/fixtures/mcp-apps/",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
