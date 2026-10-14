import { afterEach, describe, expect, it, vi } from "vitest";

import {
  MarsWebBridgeError,
  createMarsWebBridge,
  installMarsWebBridge,
  probeMarsWebBridge,
} from "#/api/mars/mars-web-bridge";
import type { Backend } from "#/api/backend-registry/types";

const sessionApiKey = vi.hoisted(() => ({ value: null as string | null }));
vi.mock("#/api/agent-server-config", () => ({
  getAgentServerHeaders: (): Record<string, string> =>
    sessionApiKey.value ? { "X-Session-API-Key": sessionApiKey.value } : {},
}));
const registered = vi.hoisted(() => ({ backends: [] as Backend[] }));
vi.mock("#/api/backend-registry/active-store", () => ({
  getRegisteredBackends: (): Backend[] => registered.backends,
}));

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  delete window.marsBridge;
  sessionApiKey.value = null;
  registered.backends = [];
});

describe("createMarsWebBridge", () => {
  it("turns each bridge call into one POST /mars/rpc/<method> carrying the arguments", async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(200, { result: { sessions: [], nextPageToken: null } }),
    );
    const bridge = createMarsWebBridge(
      "",
      fetchImpl as unknown as typeof fetch,
    );

    const page = await bridge.listConfigSessions("cfg_1", { pageSize: 5 });

    expect(fetchImpl).toHaveBeenCalledWith("/mars/rpc/listConfigSessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ args: ["cfg_1", { pageSize: 5 }] }),
    });
    expect(page).toEqual({ sessions: [], nextPageToken: null });
  });

  it("reads the sandbox size catalog over RPC", async () => {
    const sizes = [{ slug: "mars-2vcpu-4gb", vcpus: 2, memory_mb: 4096 }];
    const fetchImpl = vi.fn(async () => jsonResponse(200, { result: sizes }));
    const bridge = createMarsWebBridge(
      "",
      fetchImpl as unknown as typeof fetch,
    );

    expect(await bridge.listSandboxSizes()).toEqual(sizes);
    expect(fetchImpl).toHaveBeenCalledWith(
      "/mars/rpc/listSandboxSizes",
      expect.objectContaining({ body: JSON.stringify({ args: [] }) }),
    );
  });

  it("raises the server's error message and status", async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(401, {
        error: { message: "Sign in to DigitalOcean first.", status: 401 },
      }),
    );
    const bridge = createMarsWebBridge(
      "",
      fetchImpl as unknown as typeof fetch,
    );

    await expect(bridge.listSessions()).rejects.toMatchObject({
      name: "MarsWebBridgeError",
      message: "Sign in to DigitalOcean first.",
      status: 401,
    });
  });

  it("sends the page's session key on every call so the server can admit it", async () => {
    sessionApiKey.value = "sk-page";
    const fetchImpl = vi.fn(async () => jsonResponse(200, { result: null }));
    const bridge = createMarsWebBridge(
      "",
      fetchImpl as unknown as typeof fetch,
    );

    await bridge.pauseSession("s1");

    expect(fetchImpl).toHaveBeenCalledWith("/mars/rpc/pauseSession", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-API-Key": "sk-page",
      },
      body: JSON.stringify({ args: ["s1"] }),
    });
  });

  it("sends the key typed on the API key screen when the page has none baked in", async () => {
    const backend = (overrides: Partial<Backend>): Backend => ({
      id: "b",
      name: "b",
      host: window.location.origin,
      apiKey: "",
      kind: "local",
      ...overrides,
    });
    registered.backends = [
      backend({
        id: "remote",
        host: "http://10.0.0.9:3000",
        apiKey: "sk-remote",
      }),
      backend({ id: "mars", apiKey: "sk-mars", marsSessionId: "s1" }),
      backend({ id: "typed", apiKey: "sk-typed" }),
    ];
    const fetchImpl = vi.fn(async () => jsonResponse(200, { result: null }));
    const bridge = createMarsWebBridge(
      "",
      fetchImpl as unknown as typeof fetch,
    );

    await bridge.savePat({ token: "dop_v1_x" });

    expect(fetchImpl).toHaveBeenCalledWith(
      "/mars/rpc/savePat",
      expect.objectContaining({
        headers: {
          "Content-Type": "application/json",
          "X-Session-API-Key": "sk-typed",
        },
      }),
    );
  });

  it("never sends a key stored for another host", async () => {
    registered.backends = [
      {
        id: "remote",
        name: "remote",
        host: "http://10.0.0.9:3000",
        apiKey: "sk-remote",
        kind: "local",
      },
    ];
    const fetchImpl = vi.fn(async () => jsonResponse(200, { result: null }));
    const bridge = createMarsWebBridge(
      "",
      fetchImpl as unknown as typeof fetch,
    );

    await bridge.signOut();

    expect(fetchImpl).toHaveBeenCalledWith(
      "/mars/rpc/signOut",
      expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("never offers OAuth", async () => {
    const bridge = createMarsWebBridge("", vi.fn() as unknown as typeof fetch);
    await expect(bridge.signInWithOAuth()).rejects.toBeInstanceOf(
      MarsWebBridgeError,
    );
  });
});

describe("probeMarsWebBridge / installMarsWebBridge", () => {
  it("reports whether the server hosts the bridge", async () => {
    const ok = vi.fn(async () => jsonResponse(200, { ok: true }));
    const missing = vi.fn(async () => new Response("", { status: 404 }));
    // A server that answers every path with index.html is a 200 too.
    const spa = vi.fn(
      async () =>
        new Response("<!doctype html><title>Canvas</title>", {
          status: 200,
          headers: { "Content-Type": "text/html" },
        }),
    );
    const down = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });

    expect(await probeMarsWebBridge("", ok as unknown as typeof fetch)).toBe(
      true,
    );
    expect(
      await probeMarsWebBridge("", missing as unknown as typeof fetch),
    ).toBe(false);
    expect(await probeMarsWebBridge("", spa as unknown as typeof fetch)).toBe(
      false,
    );
    expect(await probeMarsWebBridge("", down as unknown as typeof fetch)).toBe(
      false,
    );
  });

  it("installs window.marsBridge only when the server answers, and leaves an existing bridge alone", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("", { status: 404 })),
    );
    expect(await installMarsWebBridge()).toBe(false);
    expect(window.marsBridge).toBeUndefined();

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(200, { ok: true })),
    );
    expect(await installMarsWebBridge()).toBe(true);
    expect(window.marsBridge).toBeDefined();

    const electronBridge = window.marsBridge;
    expect(await installMarsWebBridge()).toBe(false);
    expect(window.marsBridge).toBe(electronBridge);
  });
});
