import React from "react";

/**
 * Window over which a backlog is drained before the arrival rate is known.
 * Short enough that the text never visibly trails the model, long enough that
 * a burst of tokens reads as typing rather than as a paste.
 */
const DRAIN_WINDOW_MS = 120;

/**
 * Once the rate is known, the backlog is still drained at least this fast, so
 * a burst bigger than the usual chunk cannot leave the text trailing far
 * behind the model.
 */
const MAX_LAG_MS = 250;

/** Weight of the newest inter-arrival sample in the rate estimate. */
const RATE_SMOOTHING = 0.3;

/** Gaps longer than this (a pause in the model) are not a rate sample. */
const MAX_ARRIVAL_GAP_MS = 1000;

const now = () =>
  typeof performance !== "undefined" ? performance.now() : Date.now();

/**
 * Reveal `target` on a clock rather than at the granularity the network
 * happened to deliver it (#15493).
 *
 * Text is revealed at the rate it has been arriving, so chunks that land in
 * bursts read as a steady stream instead of a jump followed by a pause; a
 * backlog larger than that rate covers is drained within `MAX_LAG_MS`. Text
 * that is not an extension of what is already on screen (a superseding retry,
 * or a different slot) snaps immediately rather than being re-typed.
 */
export function useStreamedText(target: string): string {
  const [revealed, setRevealed] = React.useState(target);
  const revealedRef = React.useRef(target);
  // Fractional reveal position, so a rate of e.g. 3.4 characters per frame
  // advances evenly instead of rounding up to 4 every frame and stalling.
  const positionRef = React.useRef(target.length);
  const frameRef = React.useRef<number | null>(null);
  const arrivalRef = React.useRef<{ length: number; at: number } | null>(null);
  // Characters per millisecond, or null until two arrivals were seen.
  const rateRef = React.useRef<number | null>(null);

  React.useEffect(() => {
    const commit = (next: string) => {
      revealedRef.current = next;
      positionRef.current = next.length;
      setRevealed(next);
    };

    if (
      !target.startsWith(revealedRef.current) ||
      typeof requestAnimationFrame !== "function"
    ) {
      arrivalRef.current = null;
      rateRef.current = null;
      commit(target);
      return undefined;
    }

    const arrivedAt = now();
    const previous = arrivalRef.current;
    if (previous && target.length > previous.length) {
      const gap = arrivedAt - previous.at;
      if (gap > 0 && gap <= MAX_ARRIVAL_GAP_MS) {
        const sample = (target.length - previous.length) / gap;
        rateRef.current =
          rateRef.current === null
            ? sample
            : rateRef.current + RATE_SMOOTHING * (sample - rateRef.current);
      }
    }
    arrivalRef.current = { length: target.length, at: arrivedAt };

    if (revealedRef.current.length === target.length) {
      return undefined;
    }

    let lastTick = 0;
    const tick = (frameTime: number) => {
      frameRef.current = null;
      const elapsed = lastTick ? frameTime - lastTick : 16;
      lastTick = frameTime;

      const backlog = target.length - positionRef.current;
      const rate = rateRef.current;
      const step =
        rate === null
          ? (backlog * elapsed) / DRAIN_WINDOW_MS
          : Math.max(rate * elapsed, (backlog * elapsed) / MAX_LAG_MS);
      const position = Math.min(
        target.length,
        positionRef.current + Math.max(step, 1),
      );
      const nextLength = Math.floor(position);
      if (nextLength !== revealedRef.current.length) {
        commit(target.slice(0, nextLength));
      }
      positionRef.current = position;

      if (nextLength < target.length) {
        frameRef.current = requestAnimationFrame(tick);
      }
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
    };
  }, [target]);

  return revealed;
}
