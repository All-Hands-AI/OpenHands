// @vitest-environment node
import { copyFile, mkdir, mkdtemp, rmdir, unlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import type { Server } from "node:http";
import { describe, expect, it } from "vitest";

// @spec MCA-003 — The npm deployment retains the proxy's origin restrictions.
describe("packaged MCP App sandbox", () => {
  it("serves the built proxy when the published package has no public directory", async () => {
    const root = await mkdtemp(join(tmpdir(), "mcp-apps-packaged-"));
    const scripts = join(root, "scripts");
    const build = join(root, "build");
    const script = join(scripts, "mcp-app-sandbox.mjs");
    const html = join(build, "mcp-app-sandbox.html");
    await mkdir(scripts);
    await mkdir(build);
    await copyFile(
      new URL("../../scripts/mcp-app-sandbox.mjs", import.meta.url),
      script,
    );
    await copyFile(
      new URL("../../public/mcp-app-sandbox.html", import.meta.url),
      html,
    );
    let server: Server | undefined;
    try {
      const { createMCPAppSandboxServer } = await import(
        /* @vite-ignore */ pathToFileURL(script).href
      );
      const parentOrigin = "http://127.0.0.1:3101";
      server = await createMCPAppSandboxServer({ parentOrigin });
      await new Promise<void>((resolve) =>
        server!.listen(0, "127.0.0.1", resolve),
      );
      const address = server!.address();
      if (!address || typeof address === "string") {
        throw new Error("Sandbox listener has no TCP address");
      }
      const endpoint = `http://127.0.0.1:${address.port}/sandbox.html`;
      const response = await fetch(
        endpoint + "?parentOrigin=" + encodeURIComponent(parentOrigin),
      );

      expect(response.status).toBe(200);
      expect(response.headers.get("content-type")).toContain("text/html");
      expect(response.headers.get("cache-control")).toBe("no-store");
      expect(response.headers.get("content-security-policy")).toContain(
        "frame-ancestors " + parentOrigin,
      );
      expect(await response.text()).toContain(
        "ui/notifications/sandbox-proxy-ready",
      );
      const rejected = await fetch(
        endpoint +
          "?parentOrigin=" +
          encodeURIComponent("https://other.example"),
      );
      expect(rejected.status).toBe(404);
    } finally {
      if (server)
        await new Promise<void>((resolve) => server!.close(() => resolve()));
      await unlink(script);
      await unlink(html);
      await rmdir(build);
      await rmdir(scripts);
      await rmdir(root);
    }
  });
});
