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
  } = loadEnv(mode, process.cwd());

  const USE_TLS = VITE_USE_TLS === "true";
  const INSECURE_SKIP_VERIFY = VITE_INSECURE_SKIP_VERIFY === "true";
  const PROTOCOL = USE_TLS ? "https" : "http";
  const WS_PROTOCOL = USE_TLS ? "wss" : "ws";

  const API_URL = `${PROTOCOL}://${VITE_BACKEND_HOST}/`;
  const WS_URL = `${WS_PROTOCOL}://${VITE_BACKEND_HOST}/`;
  const FE_PORT = Number.parseInt(VITE_FRONTEND_PORT, 10);

  /**
   * This script is used to unpack the client directory from the frontend build directory.
   * Remix SPA mode builds the client directory into the build directory. This function
   * moves the contents of the client directory to the build directory and then removes the
   * client directory.
   *
   * This script is used in the buildEnd function of the Vite config.
   */
  const unpackClientDirectory = async () => {
    const fs = await import("fs");
    const path = await import("path");

    const buildDir = path.resolve(__dirname, "build");
    const clientDir = path.resolve(buildDir, "client");

    const files = await fs.promises.readdir(clientDir);
    await Promise.all(
      files.map((file) =>
        fs.promises.rename(
          path.resolve(clientDir, file),
          path.resolve(buildDir, file),
        ),
      ),
    );

    await fs.promises.rmdir(clientDir);
  };

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
          buildEnd: unpackClientDirectory,
          ssr: false,
        }),
      viteTsconfigPaths(),
      svgr(),
    ],
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
  };
});
