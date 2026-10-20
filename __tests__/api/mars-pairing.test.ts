import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BACKENDS_STORAGE_KEY } from "#/api/backend-registry/storage";
import { hadPairingFailure, redeemPairingLink } from "#/api/mars/pairing";

type StoredBackend = { id: string; host: string; apiKey: string; kind: string };

const storedBackends = (): StoredBackend[] =>
  JSON.parse(window.localStorage.getItem(BACKENDS_STORAGE_KEY) ?? "[]");

const redeemed = (key = "canvas-key") =>
  vi.fn(async () => Response.json({ result: { sessionApiKey: key } }));

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
});

afterEach(() => {
  window.history.replaceState(null, "", "/");
});

describe("redeemPairingLink", () => {
  it("leaves every other page alone", async () => {
    window.history.replaceState(null, "", "/conversations#not-a-secret");
    const fetchImpl = redeemed();

    expect(await redeemPairingLink(fetchImpl)).toBe(false);
    expect(fetchImpl).not.toHaveBeenCalled();
    expect(window.location.hash).toBe("#not-a-secret");
  });

  it("lets this device in with the key the link redeems, and clears the address bar", async () => {
    window.history.replaceState(null, "", "/pair#s3cret");
    const fetchImpl = redeemed();

    const paired = await redeemPairingLink(fetchImpl);

    expect(paired).toBe(true);
    expect(fetchImpl).toHaveBeenCalledWith(
      "/mars/pair",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ secret: "s3cret" }),
      }),
    );
    expect(`${window.location.pathname}${window.location.hash}`).toBe("/");
    const local = storedBackends().filter(
      (backend) => backend.host === window.location.origin,
    );
    expect(local).toEqual([
      expect.objectContaining({ kind: "local", apiKey: "canvas-key" }),
    ]);
  });

  it("updates the backend this address already has instead of adding one", async () => {
    window.localStorage.setItem(
      BACKENDS_STORAGE_KEY,
      JSON.stringify([
        {
          id: "mac",
          name: "Mac",
          host: window.location.origin,
          apiKey: "stale",
          kind: "local",
        },
      ]),
    );
    window.history.replaceState(null, "", "/pair#s3cret");

    await redeemPairingLink(redeemed());

    expect(storedBackends()).toEqual([
      expect.objectContaining({ id: "mac", apiKey: "canvas-key" }),
    ]);
  });

  it("notes a link that did not work, for the key screen", async () => {
    window.history.replaceState(null, "", "/pair#used");
    const fetchImpl = vi.fn(async () =>
      Response.json({ error: { message: "used" } }, { status: 400 }),
    );

    expect(await redeemPairingLink(fetchImpl)).toBe(false);
    expect(hadPairingFailure()).toBe(true);
    expect(`${window.location.pathname}${window.location.hash}`).toBe("/");
  });
});
