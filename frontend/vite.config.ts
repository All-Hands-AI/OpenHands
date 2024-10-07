/* eslint-disable import/no-extraneous-dependencies */
/// <reference types="vitest" />
/// <reference types="vite-plugin-svgr/client" />
import { defineConfig, loadEnv } from "vite";
import viteTsconfigPaths from "vite-tsconfig-paths";
import svgr from "vite-plugin-svgr";
import { vitePlugin as remix } from "@remix-run/dev";

export default defineConfig(({ mode }) => {
  const {
    VITE_BACKEND_HOST = "127.0.0.1:3000",
    VITE_USE_TLS = "false",
    VITE_FRONTEND_PORT = "3001",
    VITE_INSECURE_SKIP_VERIFY = "false",
    VITE_WATCH_USE_POLLING = "false",
  } = loadEnv(mode, process.cwd());

  const USE_TLS = VITE_USE_TLS === "true";
  const INSECURE_SKIP_VERIFY = VITE_INSECURE_SKIP_VERIFY === "true";
  const PROTOCOL = USE_TLS ? "https" : "http";
  const WS_PROTOCOL = USE_TLS ? "wss" : "ws";

  const API_URL = `${PROTOCOL}://${VITE_BACKEND_HOST}/`;
  const WS_URL = `${WS_PROTOCOL}://${VITE_BACKEND_HOST}/`;
  const FE_PORT = Number.parseInt(VITE_FRONTEND_PORT, 10);

  // check BACKEND_HOST is something like "example.com"
  if (!VITE_BACKEND_HOST.match(/^([\w\d-]+(\.[\w\d-]+)+(:\d+)?)/)) {
    throw new Error(
      `Invalid BACKEND_HOST ${VITE_BACKEND_HOST}, example BACKEND_HOST 127.0.0.1:3000`,
    );
  }

  return {
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
    server: {
      watch: {
        usePolling: VITE_WATCH_USE_POLLING === "true",
      },
      port: FE_PORT,
      proxy: {
        "/api": {
          target: API_URL,
          changeOrigin: true,
          secure: !INSECURE_SKIP_VERIFY,
        },
        "/ws": {
          target: WS_URL,
          ws: true,
          changeOrigin: true,
          secure: !INSECURE_SKIP_VERIFY,
        },
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: ["vitest.setup.ts"],
      coverage: {
        reporter: ["text", "json", "html", "lcov", "text-summary"],
        reportsDirectory: "coverage",
        include: ["src/**/*.{ts,tsx}"],
      },
    },
  };
});
