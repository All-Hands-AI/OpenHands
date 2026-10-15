import React from "react";

interface FollowStreamingReplyOptions {
  /** A reply is streaming in, so the content can grow without new events. */
  active: boolean;
  /** The user is pinned to the bottom. */
  autoScroll: boolean;
  setAutoScroll: (autoScroll: boolean) => void;
  /** Another scroll adjustment owns this frame (e.g. "load older"). */
  isPaused: () => boolean;
}

/**
 * Keep a streamed reply in view while the user is pinned to the bottom.
 *
 * The chat follows the bottom when events are added, but a streamed reply
 * grows inside a single event, so without this it runs below the fold until
 * the next event lands. The user scrolling up is read from the element each
 * frame: the `autoScroll` state that records it lags a render behind, and
 * following until then would yank them back down.
 */
export function useFollowStreamingReply(
  scrollRef: React.RefObject<HTMLElement | null>,
  { active, autoScroll, setAutoScroll, isPaused }: FollowStreamingReplyOptions,
) {
  const autoScrollRef = React.useRef(autoScroll);
  React.useLayoutEffect(() => {
    autoScrollRef.current = autoScroll;
  }, [autoScroll]);

  React.useEffect(() => {
    const dom = scrollRef.current;
    if (!active || !dom || typeof requestAnimationFrame !== "function") {
      return undefined;
    }

    let lastTop = dom.scrollTop;
    let frame = 0;
    const follow = () => {
      const bottom = dom.scrollHeight - dom.clientHeight;
      if (autoScrollRef.current && !isPaused()) {
        // Content shrinking also lowers scrollTop, but leaves it at the bottom.
        if (dom.scrollTop < lastTop - 1 && dom.scrollTop < bottom - 1) {
          autoScrollRef.current = false;
          setAutoScroll(false);
        } else if (dom.scrollTop < bottom - 1) {
          dom.scrollTop = bottom;
        }
      }
      lastTop = dom.scrollTop;
      frame = requestAnimationFrame(follow);
    };

    frame = requestAnimationFrame(follow);
    return () => cancelAnimationFrame(frame);
  }, [active, scrollRef, setAutoScroll, isPaused]);
}
