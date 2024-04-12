// eslint-disable-next-line import/no-extraneous-dependencies
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// eslint-disable-next-line import/no-extraneous-dependencies
import viteTsconfigPaths from "vite-tsconfig-paths";
import * as os from "node:os";

const BACKEND_HOST = process.env.BACKEND_HOST || "127.0.0.1:3000";

// check BACKEND_HOST is something like "example.com"
if (!BACKEND_HOST.match(/^([\w\d-]+(\.[\w\d-]+)+(:\d+)?)/)) {
  throw new Error(
    `Invalid BACKEND_HOST ${BACKEND_HOST}, example BACKEND_HOST 127.0.0.1:3000`,
  );
}

// Define separate configurations for development and production modes
let viteConfig;
// eslint-disable-next-line prefer-const
viteConfig = {
  // depending on your application, base can also be "/"
  base: "",
  outDir: "dist",
  plugins: [react(), viteTsconfigPaths()],
  clearScreen: false,
  server: {
    watch: { usePolling: true },
    port: process.env.FRONTEND_PORT
      ? Number.parseInt(process.env.FRONTEND_PORT, 10)
      : 3001,
    proxy: {
      "/api": {
        target: `http://${BACKEND_HOST}/`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/ws": {
        target: `ws://${BACKEND_HOST}/`,
        ws: true,
      },
    },
  },
  build: {
    minify: false,
    sourcemap: "inline",
    optimizeDeps: {
      include: ["lodash/fp", "src/index.tsx"],
    },
    chunkSizeWarningLimit: 2000, // Set a warning limit for chunk sizes (in bytes)
    rollupOptions: {
      external: ["src/index.tsx"],
      output: {
        manualChunks: {
          // Define manual chunks for optimization
          // For example, you can manually split React and other large dependencies into separate chunks
          react: ["react", "react-dom"],
          // Add more manual chunks as needed for other dependencies
        },
      },
    },
    server: {},
  },
};

// Conditional configuration based on NODE_ENV
if (process.env.NODE_ENV === "production") {
  // Production configuration
  viteConfig.base = "/";
  viteConfig.build.minify = true;
} else {
  // Development configuration
}

// Applied only in non-interactive environment, i.e. Docker
if (process.env.DEBIAN_FRONTEND === "noninteractive") {
  const dockerConfig = {
    server: {
      host: os.hostname(),
      origin: `http://web_ui:${process.env.UI_HTTP_PORT}`,
      port: 4173,
    },
  };

  viteConfig = { ...viteConfig, ...dockerConfig };
}

// Applied only in non-interactive environment, i.e. Docker
if (process.env.DEBIAN_FRONTEND === "noninteractive") {
  const dockerConfig = {
    server: {
      host: os.hostname(),
      origin: `http://web_ui:${process.env.UI_HTTP_PORT}`,
      port: 4173,
    },
  };

  viteConfig = Object.assign({}, ...viteConfig, ...dockerConfig);
}

export default defineConfig(viteConfig);
