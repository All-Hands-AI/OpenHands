import { getAgentServerHeaders } from "#/api/agent-server-config";
import { getRegisteredBackends } from "#/api/backend-registry/active-store";
import { buildAgentCanvasPath } from "#/utils/base-path";

export const DEVICE_PAIRING_PATH = "/pair";
export const DEVICE_PAIRING_FRAGMENT = "canvas-pair";
const PAIRING_PREFIX = "/mars/pairing/";
let pendingSecret: string | null = null;

/** Run before providers/analytics mount, keeping the one-time proof in memory. */
export function captureDevicePairingSecret(): string | null {
  if (
    typeof window === "undefined" ||
    window.location.pathname !== buildAgentCanvasPath(DEVICE_PAIRING_PATH)
  )
    return null;
  const proof = new URLSearchParams(window.location.hash.slice(1)).get(
    DEVICE_PAIRING_FRAGMENT,
  );
  if (proof) {
    pendingSecret = proof;
    window.history.replaceState(
      window.history.state,
      "",
      window.location.pathname,
    );
  }
  return pendingSecret;
}

export interface DevicePairingInvitation {
  secret: string;
  expiresAt: number;
}

/** Host access belongs to this origin, never to the selected DO guest or Cloud. */
export function getCanvasHostHeaders(): Record<string, string> {
  const baked = getAgentServerHeaders();
  if (Object.keys(baked).length > 0) return baked;
  const host = typeof window === "undefined" ? null : window.location.origin;
  const backend = getRegisteredBackends().find(
    (item) =>
      item.kind === "local" &&
      !item.marsSessionId &&
      item.host.replace(/\/+$/, "") === host,
  );
  return backend?.apiKey ? { "X-Session-API-Key": backend.apiKey } : {};
}

export function isUnencryptedNetworkUrl(value: string): boolean {
  try {
    const url = new URL(value);
    const hostname = url.hostname.replace(/^\[|\]$/g, "").toLowerCase();
    const loopback =
      hostname === "localhost" ||
      hostname.endsWith(".localhost") ||
      hostname === "::1" ||
      /^127(?:\.\d{1,3}){3}$/.test(hostname);
    return url.protocol === "http:" && !loopback;
  } catch {
    return false;
  }
}

export function buildDevicePairingLink(origin: string, secret: string): string {
  const url = new URL(origin);
  if (!/^https?:$/.test(url.protocol) || url.username || url.password)
    throw new Error("Invalid Canvas address");
  return `${url.origin}${buildAgentCanvasPath(DEVICE_PAIRING_PATH)}#${DEVICE_PAIRING_FRAGMENT}=${encodeURIComponent(secret)}`;
}

async function pairingRequest<T>(
  action: string,
  body: unknown,
  authenticated: boolean,
): Promise<T> {
  const response = await fetch(`${PAIRING_PREFIX}${action}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authenticated ? getCanvasHostHeaders() : {}),
    },
    body: JSON.stringify(body),
    cache: "no-store",
    credentials: "same-origin",
  });
  if (!response.ok) throw new Error("Device pairing failed");
  return response.json() as Promise<T>;
}

export const createDevicePairing = () =>
  pairingRequest<DevicePairingInvitation>("create", {}, true);
export const cancelDevicePairing = (secret: string) =>
  pairingRequest<unknown>("cancel", { secret }, true);
export const redeemDevicePairing = (secret: string) =>
  pairingRequest<{ sessionApiKey: string }>("redeem", { secret }, false);
