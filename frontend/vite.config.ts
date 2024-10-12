/* eslint-disable import/no-extraneous-dependencies */
/// <reference types="vitest" />
/// <reference types="vite-plugin-svgr/client" />
import { defineConfig } from "vite";
import viteTsconfigPaths from "vite-tsconfig-paths";
import svgr from "vite-plugin-svgr";
import { vitePlugin as remix } from "@remix-run/dev";

export default defineConfig(() => ({
  plugins: [
    !process.env.VITEST &&
      remix({
        future: {
          v3_fetcherPersist: true,
          v3_relativeSplatPath: true,
          v3_throwAbortReason: true,
        },
        appDirectory: "src",
        ssr: false,
      }),
    viteTsconfigPaths(),
    svgr(),
  ],
  ssr: {
    noExternal: ["react-syntax-highlighter"],
  },
  clearScreen: false,
  test: {
    environment: "jsdom",
    setupFiles: ["vitest.setup.ts"],
    coverage: {
      reporter: ["text", "json", "html", "lcov", "text-summary"],
      reportsDirectory: "coverage",
      include: ["src/**/*.{ts,tsx}"],
    },
  },
}));
