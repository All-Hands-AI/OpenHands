import { RefObject, useEffect, useState, useCallback } from "react";

export function useScrollToBottom(scrollRef: RefObject<HTMLDivElement | null>) {
  // Track whether we should auto-scroll to the bottom when content changes
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(true);

  // Track whether the user is currently at the bottom of the scroll area
  const [hitBottom, setHitBottom] = useState(true);

  // Check if the scroll position is at the bottom
  const isAtBottom = useCallback((element: HTMLElement): boolean => {
    // Use a percentage of the container height as threshold (10%)
    // This makes it "fuzzier" - user needs to scroll up more to break auto-scroll
    const bottomThresholdPercentage = 0.1; // 10% of container height
    const bottomThreshold = Math.max(
      element.clientHeight * bottomThresholdPercentage,
      20, // Minimum threshold of 20px
    );
    const bottomPosition = element.scrollTop + element.clientHeight;
    return bottomPosition >= element.scrollHeight - bottomThreshold;
  }, []);

  // Handle scroll events
  const onChatBodyScroll = useCallback(
    (e: HTMLElement) => {
      const isCurrentlyAtBottom = isAtBottom(e);
      setHitBottom(isCurrentlyAtBottom);

      // Only update shouldScrollToBottom when user manually scrolls
      // This prevents content changes from affecting our scroll behavior decision
      setShouldScrollToBottom(isCurrentlyAtBottom);
    },
    [isAtBottom],
  );

  // Scroll to bottom function with animation
  const scrollDomToBottom = useCallback(() => {
    const dom = scrollRef.current;
    if (dom) {
      requestAnimationFrame(() => {
        // Set shouldScrollToBottom to true when manually scrolling to bottom
        setShouldScrollToBottom(true);
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
    // Only auto-scroll if the user was already at the bottom
    if (shouldScrollToBottom) {
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
    autoScroll: shouldScrollToBottom,
    setAutoScroll: setShouldScrollToBottom,
    scrollDomToBottom,
    hitBottom,
    setHitBottom,
    onChatBodyScroll,
  };
}
