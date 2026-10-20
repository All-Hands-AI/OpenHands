/**
 * Main-process service behind the DigitalOcean Managed Agents screen.
 *
 * Wires the MARS REST client, the port-forward tunnel registry
 * (scripts/tunnel-registry.mjs, MARSOHS-1428/1429) and the DigitalOcean
 * credential store into Electron's IPC layer. Channel names mirror the
 * teammate fork's `window.marsBridge` surface so the two integrations stay
 * easy to reconcile.
 *
 * Connecting to a session opens a port-forward tunnel: a loopback listener
 * this process holds, relayed over harness-api's port-forward WebSocket to
 * the agent server inside the sandbox. The renderer registers the listener
 * as an ordinary local backend.
 *
 * Tokens never cross the context bridge: the renderer asks to connect by
 * session id alone, and this process sources the bearer token from the
 * stored connection for every dial. harness-api sends no CORS headers, so
 * every MARS control-plane call has to happen here anyway.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { createTunnelRegistry } from "./tunnel-registry.mjs";
import { ensureSessionAwake } from "./mars-session.mjs";
import { prepareSandbox } from "./mars-sandbox-prep.mjs";
import {
  AGENT_SERVER_GUEST_PORT,
  DEFAULT_MARS_API_BASE_URL,
  MarsApiError,
  OPENHANDS_AGENT,
  buildOpenHandsManifest,
  createMarsApiClient,
  readManifestAgent,
} from "./mars-api.mjs";
import {
  CREDENTIAL_KIND_OAUTH,
  CREDENTIAL_KIND_PAT,
  createCredentialStore,
  isValidPatFormat,
} from "./mars-credentials.mjs";
import {
  createSignInAttempts,
  exchangeCode,
  readCallback,
  refreshGrant,
  revokeToken,
  signInWithDigitalOcean,
} from "./mars-oauth.mjs";

export const MARS_TUNNEL_IPC = {
  openTunnel: "mars:openTunnel",
  closeTunnel: "mars:closeTunnel",
  getTunnel: "mars:getTunnel",
  getAuthState: "mars:getAuthState",
  signInWithOAuth: "mars:signInWithOAuth",
  savePat: "mars:savePat",
  setActiveConnection: "mars:setActiveConnection",
  signOut: "mars:signOut",
  listSessions: "mars:listSessions",
  listAgentConfigs: "mars:listAgentConfigs",
  listConfigSessions: "mars:listConfigSessions",
  listSandboxSizes: "mars:listSandboxSizes",
  createOpenHandsAgent: "mars:createOpenHandsAgent",
  createSession: "mars:createSession",
  pauseSession: "mars:pauseSession",
  resumeSession: "mars:resumeSession",
  destroySession: "mars:destroySession",
  deleteAgentConfig: "mars:deleteAgentConfig",
};

/**
 * Provisioning a brand-new sandbox is slower than waking a paused one, so the
 * create path gets a longer budget than ensureSessionAwake's wake default.
 */
const CREATE_SESSION_READY_TIMEOUT_MS = 300_000;

/**
 * createSession has just waited for READY, so the openTunnel that follows
 * within this window skips one getSession round-trip. Only that first open
 * uses it: any later one — including reusing a live tunnel — asks again, so
 * a session paused in the meantime (idle, or from another client) is woken.
 */
const READY_FRESH_MS = 10_000;

/** An OAuth access token is refreshed this long before it would expire. */
const REFRESH_EARLY_MS = 60_000;

/** How long `awaitSignIn` holds a call open before answering "pending". */
const AWAIT_SIGN_IN_MS = 20_000;

export function buildTunnelHost(localPort) {
  return `http://127.0.0.1:${localPort}`;
}

/**
 * Shipped MARS defaults from `config/defaults.json`. The packaged app copies
 * `config/` beside `scripts/`, so the same relative path works in dev and in
 * the installed bundle. A missing file only costs the OAuth button.
 *
 * @returns {{ apiBaseUrl?: string, oauthClientId?: string }}
 */
export function readMarsDefaults() {
  try {
    const defaultsPath = fileURLToPath(
      new URL("../config/defaults.json", import.meta.url),
    );
    return JSON.parse(readFileSync(defaultsPath, "utf-8")).mars ?? {};
  } catch {
    return {};
  }
}

/**
 * Env wins over shipped defaults so staging or a private OAuth app can be
 * used without rebuilding.
 *
 * @param {Record<string, string | undefined>} [env]
 * @param {{ apiBaseUrl?: string, oauthClientId?: string }} [defaults]
 */
export function readMarsConfig(
  env = process.env,
  defaults = readMarsDefaults(),
) {
  return {
    apiBaseUrl:
      env.MARS_API_BASE_URL || defaults.apiBaseUrl || DEFAULT_MARS_API_BASE_URL,
    oauthClientId: env.DO_OAUTH_CLIENT_ID || defaults.oauthClientId || null,
  };
}

/**
 * @param {object} [options]
 * @param {ReturnType<typeof createTunnelRegistry>} [options.registry] Override for tests
 * @param {ReturnType<typeof createCredentialStore>} [options.credentials] Override for tests
 * @param {ReturnType<typeof createMarsApiClient>} [options.api] Override for tests
 * @param {string} [options.userDataPath] Where the credential store lives
 * @param {import("electron").SafeStorage | null} [options.safeStorage]
 * @param {import("./mars-secret-store.mjs").SecretStore | null} [options.secrets]
 *   Where the Agent Canvas server keeps tokens (keychain, encrypted file, memory)
 * @param {(url: string) => Promise<void>} [options.openExternal] Opens the OAuth page
 * @param {typeof ensureSessionAwake} [options.ensureAwake] Override for tests
 * @param {typeof prepareSandbox} [options.prepare] Override for tests
 * @param {Record<string, string | undefined>} [options.env]
 */
export function createMarsTunnelBridge({
  registry: registryOverride,
  credentials,
  api,
  userDataPath,
  safeStorage = null,
  secrets = null,
  openExternal = async () => {},
  ensureAwake = ensureSessionAwake,
  prepare = prepareSandbox,
  env = process.env,
} = {}) {
  const config = readMarsConfig(env);
  const store =
    credentials ??
    createCredentialStore({ userDataPath, safeStorage, secrets });
  /** @param {() => string | null | Promise<string | null>} getToken */
  const clientFor = (getToken) =>
    createMarsApiClient({
      baseUrl: config.apiBaseUrl,
      deviceId: store.deviceId,
      getToken: async () => getToken(),
    });

  /** One refresh per connection at a time: a refresh token works only once. */
  const refreshing = new Map();

  /**
   * A connection's bearer token, refreshed first when it is about to expire.
   * A grant DigitalOcean no longer honours is forgotten, so the UI asks for
   * sign-in; a network failure is thrown and the saved grant kept.
   *
   * @param {string | null | undefined} id
   * @returns {Promise<string | null>}
   */
  async function tokenFor(id) {
    if (!id) return null;
    const grant = store.getGrant(id);
    if (!grant) return null;
    const expiresAt = grant.accessExpiresAt
      ? Date.parse(grant.accessExpiresAt)
      : Number.NaN;
    if (
      !grant.refreshToken ||
      Number.isNaN(expiresAt) ||
      expiresAt - Date.now() > REFRESH_EARLY_MS
    ) {
      return grant.token;
    }
    let pending = refreshing.get(id);
    if (!pending) {
      pending = refresh(id, grant).finally(() => refreshing.delete(id));
      refreshing.set(id, pending);
    }
    return pending;
  }

  async function refresh(id, grant) {
    try {
      const next = await refreshGrant({
        clientId: grant.clientId ?? config.oauthClientId,
        refreshToken: grant.refreshToken,
      });
      store.updateGrant(id, {
        token: next.accessToken,
        refreshToken: next.refreshToken,
        accessExpiresAt: next.accessExpiresAt,
        clientId: grant.clientId ?? config.oauthClientId,
      });
      return next.accessToken;
    } catch (error) {
      if (error?.isRevoked) {
        store.updateGrant(id, null);
        return null;
      }
      throw error;
    }
  }

  const client = api ?? clientFor(() => tokenFor(store.getActive()?.id));
  const attempts = createSignInAttempts();

  /** When createSession saw each session READY; see READY_FRESH_MS. */
  const readyAt = new Map();
  async function wake(options) {
    const session = await ensureAwake(options);
    readyAt.set(options.sessionId, Date.now());
    return session;
  }

  const registry =
    registryOverride ??
    createTunnelRegistry({
      ensureAwake: async ({ sessionId, getAccessToken }) => {
        // Consumed by the first open after createSession, never refreshed.
        const at = readyAt.get(sessionId);
        readyAt.delete(sessionId);
        if (at !== undefined && Date.now() - at < READY_FRESH_MS) return;
        await ensureAwake({ api: clientFor(getAccessToken), sessionId });
      },
    });

  /**
   * Sandbox preparation per session, run once per process: the fixes it
   * makes persist with the sandbox, and concurrent connects share one run.
   */
  const prepared = new Map();

  function prepareOnce(sessionId, localPort) {
    let run = prepared.get(sessionId);
    if (!run) {
      run = prepare({
        baseUrl: buildTunnelHost(localPort),
        readFailure: () => registry.get(sessionId)?.upstreamFailure,
      }).then((result) => {
        // An unreachable guest may answer next time; try again then.
        if (result === "unreachable") prepared.delete(sessionId);
        return result;
      });
      prepared.set(sessionId, run);
    }
    return run;
  }

  /** Configs are immutable, so a config's agent never needs re-reading. */
  const agentByConfigId = new Map();

  /**
   * Connect over the port-forward tunnel. `host` is what the renderer
   * registers as the backend's base URL: the loopback listener this process
   * holds for the session.
   */
  async function connectSession({ sessionId, localPort, connectionId }) {
    const getAccessToken = () => tokenFor(connectionId);
    // The guest port is fixed here rather than accepted over IPC so the
    // renderer cannot dial arbitrary ports inside the sandbox.
    let tunnel;
    try {
      tunnel = await registry.attach({
        sessionId,
        remotePort: AGENT_SERVER_GUEST_PORT,
        getAccessToken,
        apiUrl: config.apiBaseUrl,
        localPort,
        owner: connectionId,
      });
    } catch (error) {
      // A failed dial may mean the session is no longer READY; ask again.
      readyAt.delete(sessionId);
      throw error;
    }
    // Every caller gets a prepared sandbox, not just the Canvas page.
    if (tunnel.status === "connected" && tunnel.localPort !== undefined) {
      await prepareOnce(sessionId, tunnel.localPort);
    }
    return {
      ...tunnel,
      transport: "tunnel",
      host:
        tunnel.localPort === undefined
          ? undefined
          : buildTunnelHost(tunnel.localPort),
    };
  }

  /**
   * The list projection has no manifest, so each config's agent is read from
   * its full record. A failed read leaves `agent` null (unknown) and is
   * retried on the next list rather than cached.
   */
  async function withManifestAgent(config) {
    if (!agentByConfigId.has(config.id)) {
      try {
        const full = await client.getAgentConfig(config.id);
        agentByConfigId.set(config.id, readManifestAgent(full?.manifest));
      } catch {
        return { ...config, agent: null };
      }
    }
    return { ...config, agent: agentByConfigId.get(config.id) };
  }

  function authState() {
    return {
      connections: store.list(),
      active: store.getActive(),
      isPersistent: store.isPersistent,
      storage: store.storage,
      canUseOAuth: Boolean(config.oauthClientId),
    };
  }

  function requireActiveConnectionId() {
    const id = store.getActive()?.id;
    if (!id || !store.getToken(id)) {
      throw new MarsApiError("Sign in to DigitalOcean first.", { status: 401 });
    }
    return id;
  }

  /**
   * A well-formed token can still be refused by the MARS feature flippers, so
   * a new credential only sticks once a real API call has accepted it. A
   * rejected one leaves the previously active connection active.
   *
   * Once accepted, the account names the team: from the OAuth reply when
   * there is one, else from the account call. A team that already has a
   * connection keeps it (see `setTeam`). A token that may not read the
   * account keeps its label instead.
   */
  async function saveVerified(connection, account = null) {
    const previousId = store.getActive()?.id ?? null;
    const saved = store.save(connection);
    try {
      await client.verifyAccess();
    } catch (error) {
      if (!saved.reused) store.remove(saved.id);
      if (previousId) store.setActive(previousId);
      throw error;
    }
    const team = account ?? (await client.getAccount?.().catch(() => null));
    if (team) store.setTeam(saved.id, team);
    return authState();
  }

  /** @param {Awaited<ReturnType<typeof exchangeCode>>} grant */
  function saveOAuthGrant(grant, clientId) {
    return saveVerified(
      {
        kind: CREDENTIAL_KIND_OAUTH,
        token: grant.accessToken,
        refreshToken: grant.refreshToken,
        accessExpiresAt: grant.accessExpiresAt,
        clientId,
        label: "DigitalOcean",
        teamName: grant.account?.name ?? null,
      },
      grant.account,
    );
  }

  function requireOAuthClient() {
    if (!config.oauthClientId) {
      throw new MarsApiError(
        "Sign-in with DigitalOcean is not set up on this Canvas. Use a personal access token instead.",
        { status: 400 },
      );
    }
    return config.oauthClientId;
  }

  return {
    registry,

    getAuthState: authState,

    /** The desktop app's sign-in: system browser, loopback return. */
    async signInWithOAuth() {
      const clientId = requireOAuthClient();
      const grant = await signInWithDigitalOcean({ clientId, openExternal });
      return saveOAuthGrant(grant, clientId);
    },

    /**
     * Start a browser sign-in. The page opens `authorizeUrl`; DigitalOcean
     * sends the browser back to `redirectUri`, which the Canvas server
     * passes to `completeSignIn`. The PKCE proof stays here.
     *
     * @param {{ redirectUri: string }} options
     */
    beginSignIn({ redirectUri } = {}) {
      const clientId = requireOAuthClient();
      if (!redirectUri) {
        throw new MarsApiError("A sign-in needs a return address.", {
          status: 400,
        });
      }
      return attempts.begin({ clientId, redirectUri });
    },

    /**
     * How a browser sign-in stands, waiting a little for it to finish. The
     * page calls again while it reads "pending".
     *
     * @param {string} attemptId
     */
    async awaitSignIn(attemptId) {
      const result = await attempts.wait(attemptId, AWAIT_SIGN_IN_MS);
      return result.status === "done"
        ? { ...result, authState: authState() }
        : result;
    },

    /**
     * Finish a browser sign-in from the address DigitalOcean sent the
     * browser to: by the Canvas server's return route, or pasted by the user
     * when that address could not load. Works once, for an open attempt.
     *
     * @param {string} returned The return address, or just its query string
     * @param {string} [attemptId] When given, the return must belong to it
     */
    async completeSignIn(returned, attemptId) {
      const { code, state, error } = readCallback(returned);
      const attempt = attempts.claim(state, attemptId);
      if (!attempt) {
        throw new MarsApiError("This sign-in is no longer open. Start again.", {
          status: 400,
        });
      }
      try {
        if (error || !code) {
          throw new MarsApiError(error ?? "DigitalOcean sent no code back.", {
            status: 400,
          });
        }
        const grant = await exchangeCode({
          clientId: attempt.clientId,
          code,
          verifier: attempt.verifier,
          redirectUri: attempt.redirectUri,
        });
        const signedIn = await saveOAuthGrant(grant, attempt.clientId);
        attempts.succeed(attempt.id);
        return signedIn;
      } catch (failure) {
        attempts.fail(
          attempt.id,
          failure instanceof Error ? failure.message : String(failure),
        );
        throw failure;
      }
    },

    /** @param {string} attemptId */
    cancelSignIn(attemptId) {
      attempts.cancel(attemptId);
    },

    async savePat({ token, label } = {}) {
      const trimmed = token?.trim() ?? "";
      if (!isValidPatFormat(trimmed)) {
        throw new Error(
          "That does not look like a DigitalOcean personal access token.",
        );
      }
      return saveVerified({
        kind: CREDENTIAL_KIND_PAT,
        token: trimmed,
        label: label?.trim() || "DigitalOcean token",
      });
    },

    /**
     * Open tunnels are left alone: each keeps dialing with the connection
     * that opened it, since its session belongs to that connection's team.
     */
    setActiveConnection(id) {
      store.setActive(id);
      return authState();
    },

    async signOut(id) {
      const target = id ?? store.getActive()?.id;
      if (!target) return authState();
      await registry.detachOwnedBy(target);
      readyAt.clear();
      const kind = store.list().find((c) => c.id === target)?.kind;
      if (kind === CREDENTIAL_KIND_OAUTH) {
        // Revoking the refresh token ends the grant, not just this hour's token.
        const grant = store.getGrant(target);
        const token = grant?.refreshToken ?? grant?.token;
        if (token) await revokeToken(token);
      }
      store.remove(target);
      return authState();
    },

    listSessions: (options) => client.listSessions(options ?? {}),
    async listAgentConfigs(options) {
      const page = await client.listAgentConfigs(options ?? {});
      return {
        ...page,
        configs: await Promise.all(page.configs.map(withManifestAgent)),
      };
    },
    listConfigSessions: (configId, options) =>
      client.listConfigSessions(configId, options ?? {}),
    async listSandboxSizes() {
      requireActiveConnectionId();
      return client.listSandboxSizes();
    },
    pauseSession(sessionId) {
      readyAt.delete(sessionId);
      return client.pauseSession(sessionId);
    },
    resumeSession: (sessionId) => client.resumeSession(sessionId),

    /**
     * Destroy first, then drop the live connection: harness-api can refuse
     * (409 while a checkpoint/fork/rollback holds the session, 423 locked),
     * and then the session is still running and the user must keep their
     * connection to it. Only a session that is really gone is detached.
     */
    async destroySession(sessionId) {
      await client.destroySession(sessionId);
      readyAt.delete(sessionId);
      await registry.detach(sessionId);
    },
    async deleteAgentConfig(configId) {
      await client.deleteAgentConfig(configId);
      agentByConfigId.delete(configId);
    },

    /**
     * Create an OpenHands Agent Config. The manifest is built here rather
     * than accepted over IPC so the renderer can only ever create OpenHands
     * agents; it contributes just the name and an optional sandbox size slug
     * (validated by the manifest builder).
     */
    async createOpenHandsAgent({ name, size } = {}) {
      const trimmedName = name?.trim() ?? "";
      if (!trimmedName) {
        throw new MarsApiError("Give the agent a name.", { status: 400 });
      }
      const created = await client.createAgentConfig(
        trimmedName,
        buildOpenHandsManifest({ size: size || undefined }),
      );
      if (!created?.id) {
        throw new MarsApiError("DigitalOcean returned no agent.");
      }
      agentByConfigId.set(created.id, OPENHANDS_AGENT);
      return {
        id: created.id,
        name: created.name ?? trimmedName,
        created_by: created.created_by ?? null,
        updated_at: created.updated_at ?? null,
        agent: OPENHANDS_AGENT,
      };
    },

    /**
     * Launch a session from an agent config and resolve only once it is
     * READY, so the caller can tunnel to it directly. A created session
     * starts PROVISIONING, which ensureSessionAwake already polls through.
     */
    async createSession(configId, name) {
      const session = await client.createSessionFromConfig(configId, name);
      const sessionId = session?.session_id;
      if (!sessionId) {
        throw new MarsApiError("DigitalOcean returned no session.");
      }
      return wake({
        api: client,
        sessionId,
        timeoutMs: CREATE_SESSION_READY_TIMEOUT_MS,
      });
    },

    /**
     * Connect to a session's agent-server over a port-forward tunnel. The
     * connection is bound to the active credential: tunnel dials read that
     * credential's current token and are cut off when it signs out.
     */
    openTunnel({ sessionId, localPort } = {}) {
      const connectionId = requireActiveConnectionId();
      return connectSession({ sessionId, localPort, connectionId });
    },

    closeTunnel(sessionId) {
      readyAt.delete(sessionId);
      return registry.detach(sessionId);
    },
    getTunnel(sessionId) {
      return registry.get(sessionId);
    },

    /** @param {import("electron").IpcMain} ipcMain */
    registerIpc(ipcMain) {
      for (const [method, channel] of Object.entries(MARS_TUNNEL_IPC)) {
        ipcMain.handle(channel, (_event, ...args) => this[method](...args));
      }
    },

    /** Tear down every tunnel — on quit. */
    dispose() {
      return registry.detachAll();
    },
  };
}
