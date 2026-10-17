import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

/** Zombies retain a process-group id but cannot hold ports or run cleanup. */
export function groupAlive(
  pgid,
  {
    platform = process.platform,
    signal = process.kill,
    procRoot = "/proc",
    readDirectory = readdirSync,
    readStat = (path) => readFileSync(path, "utf8"),
  } = {},
) {
  if (!Number.isSafeInteger(pgid) || pgid <= 0) return false;
  try {
    signal(-pgid, 0);
  } catch (error) {
    // Permission failures do not establish that a group is dead.
    return error.code !== "ESRCH";
  }
  if (platform !== "linux") return true;
  try {
    let matched = false;
    const entries = readDirectory(procRoot).filter((name) =>
      /^\d+$/.test(name),
    );
    for (const name of entries) {
      const stat = readStat(join(procRoot, name, "stat"));
      const close = stat.lastIndexOf(")");
      const fields = stat
        .slice(close + 2)
        .trim()
        .split(/\s+/);
      if (
        close < 0 ||
        !stat.startsWith(`${name} (`) ||
        !/^[RSDZTtWXxIPK]$/.test(fields[0]) ||
        !/^\d+$/.test(fields[2])
      ) {
        return true;
      }
      if (Number(fields[2]) !== pgid) continue;
      matched = true;
      if (fields[0] !== "Z" && fields[0] !== "X" && fields[0] !== "x")
        return true;
    }
    // A disappearing/unreadable entry or a group unseen after kill(0) is an
    // incomplete observation, not permission to purge. New processes appearing
    // during the scan also prevent a negative liveness conclusion.
    const after = readDirectory(procRoot).filter((name) => /^\d+$/.test(name));
    if (
      entries.length !== after.length ||
      entries.some((name) => !after.includes(name))
    )
      return true;
    return !matched;
  } catch {
    return true;
  }
}

/** Never delete credentials/state or release a claim while a port remains open. */
export function privatePurgeAllowed(launcherStopped, ports) {
  const states = Object.values(ports);
  return (
    launcherStopped === true &&
    states.length > 0 &&
    states.every((state) => state === "closed")
  );
}
