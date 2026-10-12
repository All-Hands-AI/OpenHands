// @vitest-environment node

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { resolveAutomationKvSecret } from "../../scripts/dev-with-automation.mjs";

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
);
const entrypoint = readFileSync(
  path.join(repoRoot, "docker/entrypoint.sh"),
  "utf-8",
);

function kvSecretBlock(): string {
  const start = entrypoint.indexOf("# >>> automation-kv-secret");
  const end = entrypoint.indexOf("# <<< automation-kv-secret");
  if (start === -1 || end === -1) {
    throw new Error("Docker automation-kv-secret markers are missing");
  }
  return entrypoint.slice(start, end);
}

function dockerKvSecret(env: Record<string, string>): string {
  const result = spawnSync(
    "bash",
    [
      "-c",
      [
        "set -uo pipefail",
        "log() { :; }",
        "log_error() { :; }",
        kvSecretBlock(),
        'printf "%s" "$AUTOMATION_KV_SECRET"',
      ].join("\n"),
    ],
    { encoding: "utf-8", env: { PATH: process.env.PATH ?? "", ...env } },
  );
  expect(result.status).toBe(0);
  return result.stdout;
}

describe("Docker automation KV secret", () => {
  let stateDir = "";

  afterEach(() => {
    if (stateDir) rmSync(stateDir, { recursive: true, force: true });
  });

  function freshStateDir(): string {
    stateDir = mkdtempSync(path.join(tmpdir(), "docker-kv-secret-"));
    return stateDir;
  }

  it("keeps the first session key as the KV secret after the session key rotates", () => {
    const dir = freshStateDir();

    const first = dockerKvSecret({
      STATE_DIR: dir,
      EFFECTIVE_SESSION_KEY: "session-key-a",
    });
    const afterRotation = dockerKvSecret({
      STATE_DIR: dir,
      EFFECTIVE_SESSION_KEY: "session-key-b",
    });

    expect(first).toBe("session-key-a");
    expect(afterRotation).toBe("session-key-a");
  });

  it("prefers an explicit AUTOMATION_KV_SECRET", () => {
    const dir = freshStateDir();

    expect(
      dockerKvSecret({
        STATE_DIR: dir,
        EFFECTIVE_SESSION_KEY: "session-key-a",
        AUTOMATION_KV_SECRET: "explicit-secret",
      }),
    ).toBe("explicit-secret");
  });

  it("shares the pinned secret with the npm launcher", () => {
    const dockerFirst = freshStateDir();
    dockerKvSecret({ STATE_DIR: dockerFirst, EFFECTIVE_SESSION_KEY: "docker" });
    const npmFirst = mkdtempSync(path.join(tmpdir(), "npm-kv-secret-"));

    try {
      resolveAutomationKvSecret(
        { stateDir: npmFirst, sessionApiKey: "npm" },
        {},
      );

      expect(
        resolveAutomationKvSecret(
          { stateDir: dockerFirst, sessionApiKey: "rotated" },
          {},
        ),
      ).toBe("docker");
      expect(
        dockerKvSecret({
          STATE_DIR: npmFirst,
          EFFECTIVE_SESSION_KEY: "rotated",
        }),
      ).toBe("npm");
    } finally {
      rmSync(npmFirst, { recursive: true, force: true });
    }
  });
});
