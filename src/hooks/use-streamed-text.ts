import React from "react";
import { create } from "zustand";

/**
 * Reveal pace floor, in characters per millisecond (60 chars/s). A slow model,
 * and the last of a reply once the model has stopped, are still typed out at
 * a reading pace rather than dropped in at once.
 */
const PACE = 0.06;

/**
 * Time constant of the catch-up. Past a backlog of `PACE * MAX_LAG_MS`
 * characters the reveal drains `backlog / MAX_LAG_MS` per millisecond, so
 * while the model streams it settles at most this much of the model's output
 * behind it, which smooths the chunk cadence, and once the model stops the
 * rest is on screen within about a second and a half. It is a decay constant,
 * not a bound: at 10 s, a fast model's reply kept typing for 20-30 s after
 * the model had finished.
 */
const MAX_LAG_MS = 500;

/**
 * Hooks still revealing text, so the chat can keep following a reply that is
 * still typing out after its stream has already finished.
 */
const useRevealingStore = create<{ ids: ReadonlySet<symbol> }>(() => ({
  ids: new Set(),
}));

const setRevealing = (id: symbol, isRevealing: boolean) =>
  useRevealingStore.setState((state) => {
    if (state.ids.has(id) === isRevealing) {
      return state;
    }
    const ids = new Set(state.ids);
    if (isRevealing) {
      ids.add(id);
    } else {
      ids.delete(id);
    }
    return { ids };
  });

/** Whether any streamed text is still being revealed on screen. */
export const useIsRevealingStreamedText = () =>
  useRevealingStore((state) => state.ids.size > 0);

/**
 * Reveal `target` on a clock rather than at the granularity the network
 * happened to deliver it (#15493).
 *
 * Text is revealed at a steady pace, at least `PACE` and faster as the backlog
 * grows, so chunks that land in bursts are smoothed over `MAX_LAG_MS` instead
 * of a jump followed by a pause, and the reveal never trails the model by much
 * more than that. Text that is not an extension of what is
 * already on screen (a superseding retry, or a different slot) snaps
 * immediately rather than being re-typed.
 */
export function useStreamedText(target: string): string {
  const [revealed, setRevealed] = React.useState(target);
  const revealedRef = React.useRef(target);
  // Fractional reveal position: the pace is under one character per frame.
  const positionRef = React.useRef(target.length);
  const frameRef = React.useRef<number | null>(null);
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
      commit(target);
      return undefined;
    }
    if (revealedRef.current.length === target.length) {
      return undefined;
    }

    let lastTick = 0;
    const tick = (now: number) => {
      frameRef.current = null;
      const elapsed = lastTick ? now - lastTick : 16;
      lastTick = now;

      const backlog = target.length - positionRef.current;
      const step = Math.max(PACE, backlog / MAX_LAG_MS) * elapsed;
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
