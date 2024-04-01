import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import viteTsconfigPaths from "vite-tsconfig-paths";

const BACKEND_HOST = process.env.BACKEND_HOST || "localhost:3000";

// check BACKEND_HOST is something like "localhost:3000" or "example.com"
if (!BACKEND_HOST.match(/^(localhost|[\w\d-]+(\.[\w\d-]+)+(:\d+)?)/)) {
  throw new Error(`Invalid BACKEND_HOST ${BACKEND_HOST}, example BACKEND_HOST localhost:3000`);
}

export default defineConfig({
  // depending on your application, base can also be "/"
  base: "",
  plugins: [react(), viteTsconfigPaths()],
  server: {
    port: 3001,
    proxy: {
      "/api": {
        target: `http://${BACKEND_HOST}/`,
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/api/, ""),
      },
      "/ws": {
        target: `ws://${BACKEND_HOST}/`,
        ws: true,
      },
    },
  },
});
