// Response timing for `browser network`. Request order alone cannot show a
// race between two responses: the requests leave together and the page reads
// whichever answers first (OpenHands/OpenHands#18810). So each entry also
// records when its response headers arrived, when its body finished (or it
// failed), and its place in the order of completion.

/**
 * A recorder whose completion counter belongs to one daemon.
 * @param {() => number} now milliseconds since the epoch
 */
export function networkTiming(now = Date.now) {
  let completions = 0;
  return {
    /** A request left the page. */
    start(entry) {
      Object.defineProperty(entry, "startMs", {
        value: now(),
        enumerable: false,
      });
    },
    /** Its response headers arrived. */
    response(entry) {
      if (entry.startMs === undefined || entry.responseMs !== undefined) return;
      entry.responseMs = now() - entry.startMs;
    },
    /** Its body finished (`finished`) or the request failed (`failed`). */
    complete(entry, outcome) {
      if (entry.startMs === undefined || entry.completedSeq !== undefined)
        return;
      const at = now();
      completions += 1;
      entry.outcome = outcome;
      entry.durationMs = at - entry.startMs;
      entry.completedTs = new Date(at).toISOString();
      entry.completedSeq = completions;
    },
  };
}

/**
 * Entries in request order (the default), or by completion: completed
 * entries first in the order they completed, then those still pending in
 * request order.
 */
export function orderNetworkEntries(list, order = "request") {
  if (order === "request") return list;
  if (order !== "completion")
    throw new Error(`--order must be request or completion, got ${order}`);
  const done = list
    .filter((e) => e.completedSeq !== undefined)
    .sort((a, b) => a.completedSeq - b.completedSeq);
  return [...done, ...list.filter((e) => e.completedSeq === undefined)];
}
