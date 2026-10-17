import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "vitest";
import { groupAlive, privatePurgeAllowed } from "./lib/process-groups.mjs";

function fixture(rows) {
  const root = mkdtempSync(join(tmpdir(), "oh-process-groups-"));
  for (const [pid, group, state] of rows) {
    mkdirSync(join(root, String(pid)));
    // A legal comm may contain whitespace and closing parentheses.
    writeFileSync(
      join(root, String(pid), "stat"),
      `${pid} (worker ) helper) ${state} 1 ${group} 0 0`,
    );
  }
  return {
    root,
    options: { platform: "linux", procRoot: root, signal: () => {} },
    clean: () => rmSync(root, { recursive: true, force: true }),
  };
}

test("all zombie/dead group is stopped, but mixed live members keep it alive", () => {
  const f = fixture([
    [101, 77, "Z"],
    [102, 77, "X"],
    [103, 88, "S"],
  ]);
  try {
    assert.equal(groupAlive(77, f.options), false);
    assert.equal(groupAlive(88, f.options), true);
    writeFileSync(join(f.root, "102", "stat"), "102 (worker) S 1 77 0");
    assert.equal(groupAlive(77, f.options), true);
  } finally {
    f.clean();
  }
});

test("permission, unreadable, disappearing and unobserved groups fail closed", () => {
  const f = fixture([[101, 77, "Z"]]);
  try {
    assert.equal(
      groupAlive(77, {
        ...f.options,
        signal: () => {
          throw Object.assign(new Error(), { code: "EPERM" });
        },
      }),
      true,
    );
    assert.equal(
      groupAlive(77, {
        ...f.options,
        readStat: () => {
          throw Object.assign(new Error(), { code: "ENOENT" });
        },
      }),
      true,
    );
    assert.equal(
      groupAlive(77, {
        ...f.options,
        readDirectory: () => {
          throw new Error("denied");
        },
      }),
      true,
    );
    assert.equal(groupAlive(99, f.options), true);
    let scans = 0;
    assert.equal(
      groupAlive(77, {
        ...f.options,
        readDirectory: () => (++scans === 1 ? ["101"] : ["101", "202"]),
      }),
      true,
    );
  } finally {
    f.clean();
  }
});

test("non-Linux keeps signal-zero semantics; a missing group is stopped", () => {
  let calls = 0;
  assert.equal(
    groupAlive(77, {
      platform: "darwin",
      signal: (pid, value) => {
        assert.equal(pid, -77);
        assert.equal(value, 0);
        calls++;
      },
      readDirectory: () => {
        throw new Error("must not scan");
      },
    }),
    true,
  );
  assert.equal(calls, 1);
  assert.equal(
    groupAlive(77, {
      signal: () => {
        throw Object.assign(new Error(), { code: "ESRCH" });
      },
    }),
    false,
  );
});

test("malformed process metadata cannot authorize cleanup", () => {
  const f = fixture([[101, 77, "Z"]]);
  try {
    writeFileSync(join(f.root, "101", "stat"), "truncated");
    assert.equal(groupAlive(77, f.options), true);
  } finally {
    f.clean();
  }
});

test("private purge and claim release require a stopped group and every port closed", () => {
  const ports = { ingress: "closed", backend: "closed" };
  assert.equal(privatePurgeAllowed(true, ports), true);
  assert.equal(privatePurgeAllowed(false, ports), false);
  assert.equal(
    privatePurgeAllowed(true, { ...ports, backend: "still open" }),
    false,
  );
  assert.equal(privatePurgeAllowed(true, {}), false);
});
