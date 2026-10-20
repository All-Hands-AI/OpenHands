/**
 * Pairing another device: a device that is already in shows a one-time link
 * (`/pair#<secret>`, also as a QR code), and the new device opens it. The
 * Canvas server (scripts/mars-web-bridge.mjs) redeems the secret once, within
 * five minutes, for the same access as typing the Canvas key.
 */

import {
  DEFAULT_LOCAL_BACKEND_NAME,
  SEEDED_DEFAULT_BACKEND_ID,
} from "#/api/backend-registry/default-backend";
import {
  readStoredBackends,
  writeStoredActiveBackend,
  writeStoredBackends,
} from "#/api/backend-registry/storage";
import type { Backend } from "#/api/backend-registry/types";

/** The page a pairing link opens. */
export const PAIR_PAGE_PATH = "/pair";
const PAIR_ROUTE = "/mars/pair";
/** Set for this tab when a link did not work, so the key screen can say so. */
export const PAIRING_FAILED_STORAGE_KEY = "openhands-pairing-failed";

const originOf = (url: string): string | null => {
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
};

/** Keep the key where a typed key goes: the local backend for this origin. */
function saveLocalBackendKey(host: string, apiKey: string): void {
  const backends = readStoredBackends();
  const existing = backends.find(
    (backend) =>
      backend.kind === "local" && originOf(backend.host) === originOf(host),
  );
  const saved: Backend = existing
    ? { ...existing, apiKey }
    : {
        id: backends.some((backend) => backend.id === SEEDED_DEFAULT_BACKEND_ID)
          ? crypto.randomUUID()
          : SEEDED_DEFAULT_BACKEND_ID,
        name: DEFAULT_LOCAL_BACKEND_NAME,
        host,
        apiKey,
        kind: "local",
      };
  writeStoredBackends(
    existing
      ? backends.map((backend) => (backend.id === saved.id ? saved : backend))
      : [...backends, saved],
  );
  writeStoredActiveBackend({ backendId: saved.id });
}

/**
 * Redeem a pairing link before the app renders. The secret leaves the
 * address bar at once; it works only once anyway. Resolves true when this
 * device is now in, and the caller reloads so everything starts with the
 * saved key. A link that does not work leaves a note for the key screen.
 */
export async function redeemPairingLink(
  fetchImpl: typeof fetch = (...params) => fetch(...params),
): Promise<boolean> {
  if (window.location.pathname !== PAIR_PAGE_PATH) return false;
  const secret = window.location.hash.slice(1);
  window.history.replaceState(null, "", "/");
  try {
    const response = await fetchImpl(PAIR_ROUTE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ secret }),
    });
    const body = (await response.json()) as {
      result?: { sessionApiKey?: unknown };
    };
    const key = body.result?.sessionApiKey;
    if (!response.ok || typeof key !== "string" || !key) {
      throw new Error("pairing refused");
    }
    saveLocalBackendKey(window.location.origin, key);
    return true;
  } catch {
    try {
      window.sessionStorage.setItem(PAIRING_FAILED_STORAGE_KEY, "1");
    } catch {
      // Without storage the key screen simply shows as usual.
    }
    return false;
  }
}

/** Whether this tab arrived through a pairing link that did not work. */
export function hadPairingFailure(): boolean {
  try {
    return window.sessionStorage.getItem(PAIRING_FAILED_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}
