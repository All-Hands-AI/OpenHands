// Replays the focused browser checks without starting unrelated stack services.
import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "../../tests/e2e/mock-llm/backends",
  testMatch: "mock-llm-modified-click-tab.spec.ts",
  retries: 0,
  workers: 1,
  timeout: 20_000,
  reporter: [["list"], ["json", { outputFile: "../../.tmp/18123-native-results.json" }]],
  outputDir: "../../.tmp/18123-native-results",
  use: { trace: "off", video: "off", screenshot: "only-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
