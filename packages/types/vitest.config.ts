/// <reference types="vitest" />
import { defineConfig } from "vite";
import { configDefaults } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["vitest.setup.ts"],
    exclude: [...configDefaults.exclude],
    coverage: {
      reporter: ["text", "json", "html", "lcov", "text-summary"],
      reportsDirectory: "coverage",
      include: ["src/**/*.{ts,tsx}"],
    },
  },
});
