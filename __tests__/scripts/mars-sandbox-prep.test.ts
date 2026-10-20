// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

import {
  ENSURE_SECRET_KEY_SCRIPT,
  MARS_SANDBOX_TOOLS,
  prepareSandbox,
} from "../../scripts/mars-sandbox-prep.mjs";

const BASE = "http://127.0.0.1:51000";
const FAST = { intervalMs: 1, restartGraceMs: 1, budgetMs: 1000 };

/** A guest agent-server answering by route; `null` makes a request fail. */
function fakeGuest(routes: Record<string, unknown>) {
  const calls: { method: string; path: string; body?: unknown }[] = [];
  const fetchImpl = vi.fn(async (url: string, init: RequestInit = {}) => {
    const method = init.method ?? "GET";
    const path = new URL(url).pathname;
    calls.push({
      method,
      path,
      body: init.body ? JSON.parse(String(init.body)) : undefined,
    });
    const reply = routes[`${method} ${path}`];
    if (reply === null || reply === undefined) {
      throw new TypeError("fetch failed");
    }
    if (typeof reply === "number") return new Response("", { status: reply });
    return Response.json(reply);
  });
  return { fetchImpl: fetchImpl as unknown as typeof fetch, calls };
}

describe("prepareSandbox", () => {
  it("waits for the restarted server and moves the terminal off tmux", async () => {
    const guest = fakeGuest({
      "GET /server_info": { version: "1.56.0" },
      "POST /api/bash/execute_bash_command": { stdout: "restarting\n" },
      "GET /api/settings": { agent_settings: { tools: null } },
      "PATCH /api/settings": {},
    });

    const result = await prepareSandbox({
      baseUrl: BASE,
      readFailure: () => null,
      fetchImpl: guest.fetchImpl,
      timing: FAST,
    });

    expect(result).toBe("prepared");
    expect(guest.calls.map((call) => `${call.method} ${call.path}`)).toEqual([
      "GET /server_info",
      "POST /api/bash/execute_bash_command",
      "GET /server_info",
      "GET /api/settings",
      "PATCH /api/settings",
    ]);
    expect(guest.calls[1].body).toMatchObject({
      command: ENSURE_SECRET_KEY_SCRIPT,
    });
    expect(guest.calls[4].body).toEqual({
      agent_settings_diff: { tools: MARS_SANDBOX_TOOLS },
    });
  });

  it("leaves a ready sandbox and an explicit tool list alone", async () => {
    const guest = fakeGuest({
      "GET /server_info": { version: "1.56.0" },
      "POST /api/bash/execute_bash_command": { stdout: "ready\n" },
      "GET /api/settings": {
        agent_settings: { tools: [{ name: "terminal", params: {} }] },
      },
    });

    await prepareSandbox({
      baseUrl: BASE,
      readFailure: () => null,
      fetchImpl: guest.fetchImpl,
      timing: FAST,
    });

    expect(guest.calls.map((call) => call.method)).not.toContain("PATCH");
    expect(
      guest.calls.filter((call) => call.path === "/server_info"),
    ).toHaveLength(1);
  });

  it("never blocks connecting when the sandbox cannot be prepared", async () => {
    const guest = fakeGuest({
      "GET /server_info": { version: "1.56.0" },
      "POST /api/bash/execute_bash_command": 404,
    });

    const result = await prepareSandbox({
      baseUrl: BASE,
      readFailure: () => null,
      fetchImpl: guest.fetchImpl,
      timing: FAST,
      log: () => {},
    });

    expect(result).toBe("failed");
  });

  it("stops waiting as soon as DigitalOcean refuses the tunnel", async () => {
    const guest = fakeGuest({});

    const result = await prepareSandbox({
      baseUrl: BASE,
      readFailure: () => ({ closeCode: null, httpStatus: 403 }),
      fetchImpl: guest.fetchImpl,
      timing: { ...FAST, budgetMs: 60_000 },
    });

    expect(result).toBe("unreachable");
    expect(guest.calls).toHaveLength(1);
  });
});
