/// <reference types="vitest" />
/// <reference types="vite-plugin-svgr/client" />
import { defineConfig, loadEnv } from "vite";
import viteTsconfigPaths from "vite-tsconfig-paths";
import svgr from "vite-plugin-svgr";
import { reactRouter } from "@react-router/dev/vite";
import { configDefaults } from "vitest/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const {
    VITE_BACKEND_HOST = "127.0.0.1:3000",
    VITE_USE_TLS = "false",
    VITE_FRONTEND_PORT = "3001",
    VITE_INSECURE_SKIP_VERIFY = "false",
    VITE_APP_BASE_URL = "/",
  } = loadEnv(mode, process.cwd());

  const USE_TLS = VITE_USE_TLS === "true";
  const INSECURE_SKIP_VERIFY = VITE_INSECURE_SKIP_VERIFY === "true";
  const PROTOCOL = USE_TLS ? "https" : "http";
  const WS_PROTOCOL = USE_TLS ? "wss" : "ws";

  const API_URL = `${PROTOCOL}://${VITE_BACKEND_HOST}/`;
  const WS_URL = `${WS_PROTOCOL}://${VITE_BACKEND_HOST}/`;
  const FE_PORT = Number.parseInt(VITE_FRONTEND_PORT, 10);

  // Normalize base URL for proxy paths
  const normalizedBaseUrl = VITE_APP_BASE_URL.replace(/\/+$/, ''); // Remove trailing slashes
  const apiPath = normalizedBaseUrl === '' ? '/api' : `${normalizedBaseUrl}/api`;
  const wsPath = normalizedBaseUrl === '' ? '/ws' : `${normalizedBaseUrl}/ws`;
  const socketIoPath = normalizedBaseUrl === '' ? '/socket.io' : `${normalizedBaseUrl}/socket.io`;

  // Create dynamic proxy configuration based on base URL
  const proxyConfig: Record<string, any> = {};

  // API proxy
  proxyConfig[apiPath] = {
    target: API_URL,
    changeOrigin: true,
    secure: !INSECURE_SKIP_VERIFY,
    rewrite: normalizedBaseUrl ? (path: string) => path.replace(new RegExp(`^${normalizedBaseUrl}`), '') : undefined,
  };

  // WebSocket proxy
  proxyConfig[wsPath] = {
    target: WS_URL,
    ws: true,
    changeOrigin: true,
    secure: !INSECURE_SKIP_VERIFY,
    rewrite: normalizedBaseUrl ? (path: string) => path.replace(new RegExp(`^${normalizedBaseUrl}`), '') : undefined,
  };

  // Socket.IO proxy
  proxyConfig[socketIoPath] = {
    target: WS_URL,
    ws: true,
    changeOrigin: true,
    secure: !INSECURE_SKIP_VERIFY,
    rewrite: normalizedBaseUrl ? (path: string) => path.replace(new RegExp(`^${normalizedBaseUrl}`), '') : undefined,
  };

  return {
    base: VITE_APP_BASE_URL,
    publicDir: "public",
    plugins: [
      !process.env.VITEST && reactRouter({
        basename: VITE_APP_BASE_URL,
      }),
      viteTsconfigPaths(),
      svgr(),
      tailwindcss(),
    ],
    define: {
      // Expose the base URL to the frontend for runtime API calls
      __VITE_APP_BASE_URL__: JSON.stringify(VITE_APP_BASE_URL),
    },
    server: {
      port: FE_PORT,
      host: true,
      allowedHosts: true,
      proxy: proxyConfig,
      watch: {
        ignored: ["**/node_modules/**", "**/.git/**"],
      },
    },
    ssr: {
      noExternal: ["react-syntax-highlighter"],
    },
    clearScreen: false,
    test: {
      environment: "jsdom",
      setupFiles: ["vitest.setup.ts"],
      exclude: [...configDefaults.exclude, "tests"],
      coverage: {
        reporter: ["text", "json", "html", "lcov", "text-summary"],
        reportsDirectory: "coverage",
        include: ["src/**/*.{ts,tsx}"],
      },
    },
  };
});
