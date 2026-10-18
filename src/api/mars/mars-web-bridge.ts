/**
 * `window.marsBridge` for the web build.
 *
 * The desktop app gets the bridge from Electron's preload; a browser gets it
 * from the Agent Canvas server instead, which hosts the same main-process
 * bridge and exposes it same-origin under `/mars/rpc/<method>` (see
 * scripts/mars-web-bridge.mjs). Every method here is one POST carrying the
 * call's arguments, so the rest of the Managed Agents UI runs unchanged: it
 * only ever talks to the `MarsBridge` interface.
 *
 * Connections resolve to a path-prefixed backend on this origin
 * (`/mars/sessions/<id>`), which the server proxies to the port-forward
 * tunnel it holds for the session. The DigitalOcean token is used only on the
 * server to dial that tunnel and never reaches the page.
 *
 * The server wants its session key on these routes. Each RPC carries it as
 * `X-Session-API-Key` (the key this page already holds for the agent-server);
 * the server answers with an HttpOnly cookie that the browser then sends by
 * itself on the proxied REST calls and the WebSocket upgrade.
 */

import {
  getAgentServerBaseUrl,
  getBakedSessionApiKey,
  isServedOriginHost,
} from "#/api/agent-server-config";
import { setRegisteredBackends } from "#/api/backend-registry/active-store";
import {
  DEFAULT_LOCAL_BACKEND_NAME,
  SEEDED_DEFAULT_BACKEND_ID,
} from "#/api/backend-registry/default-backend";
import { readStoredBackends } from "#/api/backend-registry/storage";
import type { Backend } from "#/api/backend-registry/types";
import type { MarsBridge } from "./mars-tunnel-backend";

export const MARS_WEB_HEALTH_PATH = "/mars/health";
const RPC_PREFIX = "/mars/rpc/";
const PROBE_TIMEOUT_MS = 1_500;
/** Header name carrying the hosting session key on `/mars/rpc/*`. */
const REQUEST_KEY_HEADER = "x-session-api-key";

/** Last `/mars/health` `authRequired` signal seen by the probe. */
let lastProbeAuthRequired = false;

interface RpcEnvelope<T> {
  result?: T;
  error?: { message?: string; status?: number };
}

/** A bridge call the server refused; `status` is the HTTP status it chose. */
export class MarsWebBridgeError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "MarsWebBridgeError";
    this.status = status;
  }
}

/**
 * Return headers required to authenticate with the Agent Canvas MARS web bridge.
 *
 * Attaches the session API key configured for the page's served origin:
 * 1. Uses the baked session API key if present (e.g. default launcher).
 * 2. Otherwise falls back to the key the user typed for the page's origin on the API key screen
 *    (stored on the local backend in the backend registry).
 * 3. Never attaches a key if baseUrl points to a different host (foreign backend), or if
 *    the stored key belongs to a different host.
 */
export function getMarsBridgeHeaders(baseUrl = ""): Record<string, string> {
  if (baseUrl && !isServedOriginHost(baseUrl)) {
    return {};
  }

  const bakedKey = getBakedSessionApiKey();
  if (bakedKey) {
    return { "X-Session-API-Key": bakedKey };
  }

  const backends = readStoredBackends();
  const servedBackend = backends.find(
    (b) =>
      b.kind === "local" &&
      isServedOriginHost(b.host) &&
      b.apiKey.trim().length > 0,
  );

  if (servedBackend) {
    return { "X-Session-API-Key": servedBackend.apiKey.trim() };
  }

  return {};
}

async function rpc<T>(
  baseUrl: string,
  method: string,
  args: unknown[],
  fetchImpl: typeof fetch,
): Promise<T> {
  const response = await fetchImpl(`${baseUrl}${RPC_PREFIX}${method}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getMarsBridgeHeaders(baseUrl),
    },
    body: JSON.stringify({ args }),
  });
  let envelope: RpcEnvelope<T> = {};
  try {
    envelope = (await response.json()) as RpcEnvelope<T>;
  } catch {
    // A non-JSON body (edge error page) falls through to the status line.
  }
  if (!response.ok) {
    throw new MarsWebBridgeError(
      envelope.error?.message ?? `${response.status} ${response.statusText}`,
      envelope.error?.status ?? response.status,
    );
  }
  return envelope.result as T;
}

/**
 * @param baseUrl Origin (and path prefix) the Agent Canvas server is on;
 *   empty means the page's own origin.
 */
export function createMarsWebBridge(
  baseUrl = "",
  fetchImpl: typeof fetch = (...params) => fetch(...params),
): MarsBridge {
  const call =
    <T>(method: string) =>
    (...args: unknown[]) =>
      rpc<T>(baseUrl, method, args, fetchImpl);
  return {
    getAuthState: call("getAuthState"),
    // The web server never offers OAuth (no trusted loopback redirect); the
    // auth state it returns says so, and the UI hides the button.
    signInWithOAuth: async () => {
      throw new MarsWebBridgeError(
        "OAuth sign-in is only available in the desktop app; use a personal access token.",
        400,
      );
    },
    savePat: call("savePat"),
    setActiveConnection: call("setActiveConnection"),
    signOut: call("signOut"),
    listSessions: call("listSessions"),
    listAgentConfigs: call("listAgentConfigs"),
    listConfigSessions: call("listConfigSessions"),
    listSandboxSizes: call("listSandboxSizes"),
    createOpenHandsAgent: call("createOpenHandsAgent"),
    createSession: call("createSession"),
    pauseSession: call("pauseSession"),
    resumeSession: call("resumeSession"),
    destroySession: call("destroySession"),
    deleteAgentConfig: call("deleteAgentConfig"),
    openTunnel: call("openTunnel"),
    closeTunnel: call("closeTunnel"),
    getTunnel: call("getTunnel"),
  };
}

/** Whether the server this page came from hosts the MARS web bridge. */
export async function probeMarsWebBridge(
  baseUrl = "",
  fetchImpl: typeof fetch = (...params) => fetch(...params),
  timeoutMs = PROBE_TIMEOUT_MS,
): Promise<boolean> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(`${baseUrl}${MARS_WEB_HEALTH_PATH}`, {
      signal: controller.signal,
    });
    if (!response.ok) return false;
    // A server that answers every path with index.html is also a 200; only
    // the bridge says `{ ok: true }`.
    try {
      const body = (await response.json()) as {
        ok?: unknown;
        authRequired?: unknown;
      };
      lastProbeAuthRequired = body.authRequired === true;
      return body?.ok === true;
    } catch {
      return false;
    }
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Install the web bridge as `window.marsBridge` when this page is served by
 * an Agent Canvas server that hosts it. A no-op in Electron (the preload has
 * already provided the bridge) and when the server does not offer MARS, so
 * the Managed Agents UI stays hidden exactly as before. Resolves before the
 * app renders because `getMarsBridge()` is read synchronously.
 */
export async function installMarsWebBridge(): Promise<boolean> {
  if (typeof window === "undefined" || window.marsBridge) return false;
  if (!(await probeMarsWebBridge())) return false;
  window.marsBridge = createMarsWebBridge();
  return true;
}

/** Auth posture of the page's own MARS bridge routes. */
export interface MarsWebBridgeAuth {
  /** `/mars/*` routes sit behind the server's session key. */
  required: boolean;
  /** The page has no key to present (no baked key, no stored served-origin key). */
  missing: boolean;
}

/**
 * Determine whether the page's own bridge needs a session key the page cannot
 * currently supply, using the same headers `rpc()` would send.
 *
 * `authRequired` is the bridge's own `/mars/health` `authRequired` signal (the
 * RPC routes 401 without the key). `missing` is whether those headers carry no
 * key — neither a baked key nor a stored served-origin key. On a fresh keyed
 * non-loopback bind both are true: the bridge is mounted, the page has no key,
 * and any `/mars/rpc/*` call would fail 401.
 *
 * Honest under-reporting (ambient auth reads as available) is preferred over
 * flipping an existing self-configuring setup to a dead-end key prompt.
 */
export function resolveMarsWebBridgeAuth(
  authRequired: boolean,
  options: { headers?: Record<string, string> } = {},
): MarsWebBridgeAuth {
  if (!authRequired) return { required: false, missing: false };
  const headers =
    options.headers ??
    (typeof window !== "undefined" ? getMarsBridgeHeaders() : {});
  const hasKey = Object.keys(headers).some(
    (name) => name.toLowerCase() === REQUEST_KEY_HEADER,
  );
  return { required: true, missing: !hasKey };
}

/**
 * The `authRequired` flag the page's own bridge reported during probing. Used
 * for the onboarding hosting-auth-first gate without re-issuing the request.
 */
export function getMarsWebBridgeAuthRequired(): boolean {
  return lastProbeAuthRequired;
}

/**
 * Pass the hosting session key to the bridge immediately, then hand it to the
 * backend registry so subsequent pages reload onto an authenticated hosted
 * bridge. The key is treated purely as the bridge/host credential (never the
 * DigitalOcean token and never a guest backend key).
 */
export async function saveHostingSessionKey(
  key: string,
  selectors?: { fetch?: typeof fetch },
): Promise<void> {
  const fetchImpl = selectors?.fetch ?? fetch;
  const response = await fetchImpl(`${RPC_PREFIX}getAuthState`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-API-Key": key,
    },
    body: JSON.stringify({ args: [] }),
  });
  if (!response.ok) {
    throw new MarsWebBridgeError(
      response.status === 401
        ? "session key required"
        : String(response.status),
      response.status,
    );
  }
  installServedOriginSessionKey(key);
}

/**
 * Persist the hosting session key onto the active served-origin local backend
 * so `getMarsBridgeHeaders()` (and the app's own `/server_info` auth) picks it
 * up on the next rendering pass. `getMarsBridgeHeaders()` looks the key up on
 * the *active* local backend, so this must write through `setRegisteredBackends`
 * (which notifies the active store) rather than `writeStoredBackends` alone.
 */
function installServedOriginSessionKey(key: string): void {
  const baseUrl = getAgentServerBaseUrl();
  if (!baseUrl) return;

  const backends = readStoredBackends();
  const target = backends.find(
    (b) => b.kind === "local" && isServedOriginHost(b.host),
  );
  if (target) {
    setRegisteredBackends(
      backends.map((b) =>
        b.id === target.id ? { ...b, apiKey: key.trim() } : b,
      ),
    );
    return;
  }

  const fallback: Backend = {
    id: SEEDED_DEFAULT_BACKEND_ID,
    name: DEFAULT_LOCAL_BACKEND_NAME,
    host: baseUrl,
    apiKey: key.trim(),
    kind: "local",
    // `authMode` is optional on `Backend`; omit it so the entry reads exactly
    // like other user-created local backends (the registry validates both
    // `undefined` and `"api-key"`).
  };
  setRegisteredBackends([fallback, ...backends]);
}
