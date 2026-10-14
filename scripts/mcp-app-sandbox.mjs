import http from "node:http";
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const SANDBOX_PATH = "/sandbox.html";
const PARENT_ORIGIN_PARAM = "parentOrigin";
const DEFAULT_PORT = 3102;
const DEFAULT_HOST = "127.0.0.1";
const SANDBOX_FILE = new URL("../public/mcp-app-sandbox.html", import.meta.url);
const PACKAGED_SANDBOX_FILE = new URL(
  "../build/mcp-app-sandbox.html",
  import.meta.url,
);

// @spec MCA-003 — The proxy lives on a separate, credential-free origin.
export async function createMCPAppSandboxServer({ parentOrigin }) {
  const parent = new URL(parentOrigin);
  if (
    !["http:", "https:"].includes(parent.protocol) ||
    parent.origin !== parentOrigin ||
    parent.username ||
    parent.password
  ) {
    throw new Error("A plain HTTP(S) parent origin is required");
  }
  const html = await readFile(SANDBOX_FILE).catch((error) => {
    if (error.code !== "ENOENT") throw error;
    // npm publishes build rather than the source public directory.
    return readFile(PACKAGED_SANDBOX_FILE);
  });
  return http.createServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://sandbox.invalid");
    response.setHeader("Cache-Control", "no-store");
    response.setHeader("X-Content-Type-Options", "nosniff");
    response.setHeader("Referrer-Policy", "no-referrer");
    response.setHeader(
      "Permissions-Policy",
      "camera=(), microphone=(), geolocation=(), clipboard-write=(), fullscreen=()",
    );
    if (
      request.method !== "GET" ||
      url.pathname !== SANDBOX_PATH ||
      url.searchParams.get(PARENT_ORIGIN_PARAM) !== parentOrigin
    ) {
      response.writeHead(404).end();
      return;
    }
    // srcdoc inherits this policy; inline scripts are needed by self-contained
    // Apps. Only the trusted proxy document is ever served on this origin.
    response.setHeader(
      "Content-Security-Policy",
      [
        "default-src 'none'",
        "script-src 'unsafe-inline'",
        "style-src 'unsafe-inline'",
        "img-src data: blob:",
        "font-src data:",
        "media-src data: blob:",
        "connect-src 'none'",
        "worker-src 'none'",
        "frame-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
        `frame-ancestors ${parentOrigin}`,
      ].join("; "),
    );
    response.setHeader("Content-Type", "text/html; charset=utf-8");
    response.end(html);
  });
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  const args = process.argv.slice(2);
  const option = (name, fallback) => {
    const index = args.indexOf(name);
    return index < 0 ? fallback : args[index + 1];
  };
  const parentOrigin = option("--parent-origin", "http://127.0.0.1:3101");
  const port = Number(option("--port", DEFAULT_PORT));
  const host = option("--host", DEFAULT_HOST);
  if (!Number.isInteger(port) || port < 1 || port > 65535 || !host) {
    throw new Error("Invalid sandbox bind address");
  }
  const server = await createMCPAppSandboxServer({ parentOrigin });
  server.listen(port, host, () => {
    process.stdout.write(
      `MCP App sandbox: http://${host}:${port}${SANDBOX_PATH}\n`,
    );
  });
  const stop = () => server.close();
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);
}
