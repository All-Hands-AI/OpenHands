import React from "react";

/**
 * Fastest steady reveal, in characters per millisecond (120 chars/s). Fast
 * models deliver several hundred characters a second; revealing at that pace
 * reads as text being dumped rather than written.
 */
const MAX_PACE = 0.12;

/**
 * How far the reveal may trail the model before it speeds up beyond
 * `MAX_PACE`: past this backlog, it drains at least `backlog / MAX_LAG_MS`, so
 * a long reply from a fast model never ends up more than a few seconds behind.
 */
const MAX_LAG_MS = 5000;

/** Weight of the newest inter-arrival sample in the rate estimate. */
const RATE_SMOOTHING = 0.3;

/** Gaps longer than this (a pause in the model) are not a rate sample. */
const MAX_ARRIVAL_GAP_MS = 1000;

const now = () =>
  typeof performance !== "undefined" ? performance.now() : Date.now();

// Hooks that are still revealing text, so the chat can keep following a reply
// that is still typing out after its stream has already finished.
const revealing = new Set<symbol>();
const revealingListeners = new Set<() => void>();

const setRevealing = (id: symbol, isRevealing: boolean) => {
  const wasRevealing = revealing.size > 0;
  if (isRevealing) {
    revealing.add(id);
  } else {
    revealing.delete(id);
  }
  if (wasRevealing !== revealing.size > 0) {
    revealingListeners.forEach((listener) => listener());
  }
};

const subscribeRevealing = (listener: () => void) => {
  revealingListeners.add(listener);
  return () => {
    revealingListeners.delete(listener);
  };
};

/** Whether any streamed text is still being revealed on screen. */
export function useIsRevealingStreamedText(): boolean {
  return React.useSyncExternalStore(
    subscribeRevealing,
    () => revealing.size > 0,
    () => false,
  );
}

/**
 * Reveal `target` on a clock rather than at the granularity the network
 * happened to deliver it (#15493).
 *
 * Text is revealed at the rate it has been arriving, capped at `MAX_PACE`, so
 * chunks that land in bursts read as steady writing instead of a jump followed
 * by a pause; only a backlog worth more than `MAX_LAG_MS` speeds it up. Text
 * that is not an extension of what is already on screen (a superseding retry,
 * or a different slot) snaps immediately rather than being re-typed.
 */
export function useStreamedText(target: string): string {
  const [revealed, setRevealed] = React.useState(target);
  const revealedRef = React.useRef(target);
  // Fractional reveal position, so a pace of e.g. 1.9 characters per frame
  // advances evenly instead of rounding every frame.
  const positionRef = React.useRef(target.length);
  const frameRef = React.useRef<number | null>(null);
  const arrivalRef = React.useRef<{ length: number; at: number } | null>(null);
  // Characters per millisecond, or null until two arrivals were seen.
  const rateRef = React.useRef<number | null>(null);
  const [revealId] = React.useState(() => Symbol("streamed-text"));

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
      const pace = Math.min(rateRef.current ?? MAX_PACE, MAX_PACE);
      const step = Math.max(pace, backlog / MAX_LAG_MS) * elapsed;
      const position = Math.min(target.length, positionRef.current + step);
      const nextLength = Math.floor(position);
      if (nextLength !== revealedRef.current.length) {
        commit(target.slice(0, nextLength));
      }
      positionRef.current = position;

      if (nextLength < target.length) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        setRevealing(revealId, false);
      }
    };

    setRevealing(revealId, true);
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      setRevealing(revealId, false);
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
    };
  }, [target, revealId]);

  return revealed;
}
