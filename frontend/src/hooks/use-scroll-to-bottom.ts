import { RefObject, useEffect, useState, useCallback } from "react";

export function useScrollToBottom(scrollRef: RefObject<HTMLDivElement | null>) {
  // Track whether we should auto-scroll to the bottom when content changes
  const [shouldScrollToBottom, setShouldScrollToBottom] = useState(true);

  // Track whether the user is currently at the bottom of the scroll area
  const [hitBottom, setHitBottom] = useState(true);

  // Check if the scroll position is at the bottom
  const isAtBottom = useCallback((element: HTMLElement): boolean => {
    const bottomThreshold = 50; // Increased threshold to be more lenient
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
        // Use a short timeout to ensure content has been rendered
        setTimeout(() => {
          requestAnimationFrame(() => {
            dom.scrollTo({
              top: dom.scrollHeight,
              behavior: "smooth",
            });
            // Check if we actually reached the bottom
            if (isAtBottom(dom)) {
              setHitBottom(true);
            }
          });
        }, 50);
      }
    }
  }, [scrollRef, shouldScrollToBottom, isAtBottom]);

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
