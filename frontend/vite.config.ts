/// <reference types="vitest" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import viteTsconfigPaths from "vite-tsconfig-paths";
import path from "path";

export default defineConfig(({ mode }) => {
  const {
    VITE_BACKEND_HOST = "127.0.0.1:3000",
    VITE_USE_TLS = "false",
    VITE_FRONTEND_PORT = "3001",
    VITE_INSECURE_SKIP_VERIFY = "false",
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
    // depending on your application, base can also be "/"
    base: "",
    plugins: [react(), viteTsconfigPaths()],
    clearScreen: false,
    server: {
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
      globals: true,
      setupFiles: ["vitest.setup.ts"],
    },
  };
});
