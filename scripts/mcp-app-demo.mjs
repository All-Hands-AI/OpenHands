import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { createServer } from "vite";
import svgr from "vite-plugin-svgr";
import tailwindcss from "@tailwindcss/vite";
import { createMCPAppSandboxServer } from "./mcp-app-sandbox.mjs";

const APP_HOST = "127.0.0.1";
const APP_PORT = 3101;
const SANDBOX_PORT = 3102;
const APP_ORIGIN = `http://${APP_HOST}:${APP_PORT}`;
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const sandbox = await createMCPAppSandboxServer({ parentOrigin: APP_ORIGIN });
await new Promise((resolveListen, reject) => {
  sandbox.once("error", reject);
  sandbox.listen(SANDBOX_PORT, APP_HOST, resolveListen);
});

const vite = await createServer({
  configFile: false,
  root,
  appType: "spa",
  plugins: [svgr(), tailwindcss()],
  define: { __EXTENSIONS_SKILLS_DIR__: JSON.stringify("") },
  resolve: {
    alias: { "#": resolve(root, "src") },
  },
  server: {
    host: APP_HOST,
    port: APP_PORT,
    strictPort: true,
    fs: { allow: [root] },
  },
});

try {
  await vite.listen();
} catch (error) {
  sandbox.close();
  throw error;
}

process.stdout.write(
  `MCP Apps prototype: ${APP_ORIGIN}/src/fixtures/mcp-apps/\n`,
);
process.stdout.write(
  `MCP App sandbox: http://${APP_HOST}:${SANDBOX_PORT}/sandbox.html\n`,
);

let closing = false;
const close = async () => {
  if (closing) return;
  closing = true;
  await Promise.all([
    vite.close(),
    new Promise((resolveClose) => sandbox.close(resolveClose)),
  ]);
};
process.once("SIGINT", () => void close());
process.once("SIGTERM", () => void close());
