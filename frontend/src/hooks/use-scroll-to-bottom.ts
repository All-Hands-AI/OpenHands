import { RefObject, useEffect, useState, useCallback, useRef } from "react";

export function useScrollToBottom(scrollRef: RefObject<HTMLDivElement | null>) {
  // Track whether we should auto-scroll to the bottom when content changes
  const [autoscroll, setAutoscroll] = useState(true);

  // Track whether the user is currently at the bottom of the scroll area
  const [hitBottom, setHitBottom] = useState(true);

  // Store previous scroll position to detect scroll direction
  const prevScrollTopRef = useRef<number>(0);

  // Check if the scroll position is at the bottom
  const isAtBottom = useCallback((element: HTMLElement): boolean => {
    // Use a fixed 20px buffer
    const bottomThreshold = 20;
    const bottomPosition = element.scrollTop + element.clientHeight;
    return bottomPosition >= element.scrollHeight - bottomThreshold;
  }, []);

  // Handle scroll events
  const onChatBodyScroll = useCallback(
    (e: HTMLElement) => {
      const isCurrentlyAtBottom = isAtBottom(e);
      setHitBottom(isCurrentlyAtBottom);

      // Get current scroll position
      const currentScrollTop = e.scrollTop;

      // Detect scroll direction
      const isScrollingUp = currentScrollTop < prevScrollTopRef.current;

      // Update previous scroll position for next comparison
      prevScrollTopRef.current = currentScrollTop;

      // Turn off autoscroll only when scrolling up
      if (isScrollingUp) {
        setAutoscroll(false);
      }

      // Turn on autoscroll when scrolled to the bottom
      if (isCurrentlyAtBottom) {
        setAutoscroll(true);
      }
    },
    [isAtBottom],
  );

  // Scroll to bottom function with animation
  const scrollDomToBottom = useCallback(() => {
    const dom = scrollRef.current;
    if (dom) {
      requestAnimationFrame(() => {
        // Set autoscroll to true when manually scrolling to bottom
        setAutoscroll(true);
        setHitBottom(true);

        // Use smooth scrolling but with a fast duration
        dom.scrollTo({
          top: dom.scrollHeight,
          behavior: "smooth",
        });
      });
    }
  }, [scrollRef]);

  // Auto-scroll effect that runs when content changes
  useEffect(() => {
    // Only auto-scroll if autoscroll is enabled
    if (autoscroll) {
      const dom = scrollRef.current;
      if (dom) {
        requestAnimationFrame(() => {
          dom.scrollTo({
            top: dom.scrollHeight,
            behavior: "smooth",
          });
        });
      }
    }
  });

  return {
    scrollRef,
    autoScroll: autoscroll,
    setAutoScroll: setAutoscroll,
    scrollDomToBottom,
    hitBottom,
    setHitBottom,
    onChatBodyScroll,
  };
}
