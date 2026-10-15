import { findFreePorts } from "../../../../scripts/dev-safe.mjs";

/**
 * Env var holding the ports chosen by the first evaluation of a mock-LLM
 * Playwright config. Workers re-import that config after webServers bind, so
 * a second findFreePorts() pass treats the live ports as busy and points
 * baseURL / MOCK_LLM_BACKEND_URL at a different set. The snapshot is copied
 * into the worker via process.env at fork time. A file under RUN_ROOT would
 * not survive: the webServer command deletes RUN_ROOT before workers start.
 */
export const MOCK_LLM_PORT_SNAPSHOT_ENV = "MOCK_LLM_PORT_SNAPSHOT";

type PortSnapshot = {
  scope: string;
  ports: Record<string, number>;
};

function readPortSnapshot(raw: string | undefined): PortSnapshot | undefined {
  const trimmed = raw?.trim();
  if (!trimmed) return undefined;

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error(`${MOCK_LLM_PORT_SNAPSHOT_ENV} is not valid JSON`);
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${MOCK_LLM_PORT_SNAPSHOT_ENV} must be a JSON object`);
  }

  const record = parsed as { scope?: unknown; ports?: unknown };
  if (typeof record.scope !== "string" || !record.scope) {
    throw new Error(`${MOCK_LLM_PORT_SNAPSHOT_ENV} is missing a scope`);
  }
  if (
    !record.ports ||
    typeof record.ports !== "object" ||
    Array.isArray(record.ports)
  ) {
    throw new Error(`${MOCK_LLM_PORT_SNAPSHOT_ENV} is missing ports`);
  }

  const ports: Record<string, number> = {};
  for (const [name, value] of Object.entries(record.ports)) {
    const port = typeof value === "number" ? value : Number(value);
    if (!Number.isInteger(port) || port <= 0 || port > 65535) {
      throw new Error(
        `${MOCK_LLM_PORT_SNAPSHOT_ENV} has an invalid port for "${name}"`,
      );
    }
    ports[name] = port;
  }
  return { scope: record.scope, ports };
}

/**
 * Allocate each port once per process tree. Later evaluations, including
 * Playwright workers, reuse the snapshot instead of probing again.
 * Explicit preferred values apply only to the first allocation.
 */
export async function allocateMockLlmPorts<Name extends string>(
  specs: Array<{ name: Name; envName: string; preferred: number }>,
  scope: string,
  env: NodeJS.ProcessEnv = process.env,
): Promise<Record<Name, string>> {
  const snapshot = readPortSnapshot(env[MOCK_LLM_PORT_SNAPSHOT_ENV]);
  if (snapshot?.scope === scope) {
    const missing = specs.filter(
      (spec) => snapshot.ports[spec.name] === undefined,
    );
    if (missing.length > 0) {
      throw new Error(
        `${MOCK_LLM_PORT_SNAPSHOT_ENV} is missing ${missing
          .map((spec) => spec.name)
          .join(", ")}`,
      );
    }
    return applySnapshot(specs, snapshot.ports, env);
  }

  const allocated = await findFreePorts(
    specs.map((spec) => ({ name: spec.name, preferred: spec.preferred })),
  );
  const chosen: Record<string, number> = {};
  for (const spec of specs) {
    const port = allocated[spec.name];
    if (typeof port !== "number") {
      throw new Error(`findFreePorts did not allocate "${spec.name}"`);
    }
    chosen[spec.name] = port;
  }
  Object.assign(env, {
    [MOCK_LLM_PORT_SNAPSHOT_ENV]: JSON.stringify({ scope, ports: chosen }),
  });
  return applySnapshot(specs, chosen, env);
}

function applySnapshot<Name extends string>(
  specs: Array<{ name: Name; envName: string }>,
  snapshot: Record<string, number>,
  env: NodeJS.ProcessEnv,
): Record<Name, string> {
  const ports = {} as Record<Name, string>;
  const updates: Record<string, string> = {};
  for (const spec of specs) {
    const value = String(snapshot[spec.name]);
    updates[spec.envName] = value;
    ports[spec.name] = value;
  }
  Object.assign(env, updates);
  return ports;
}
