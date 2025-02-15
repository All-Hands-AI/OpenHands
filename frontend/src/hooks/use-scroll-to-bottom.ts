import { RefObject, useEffect, useState } from "react";

export function useScrollToBottom(scrollRef: RefObject<HTMLDivElement | null>) {
  // for auto-scroll

  const [autoScroll, setAutoScroll] = useState(true);
  const [hitBottom, setHitBottom] = useState(true);

  const onChatBodyScroll = (e: HTMLElement) => {
    const bottomHeight = e.scrollTop + e.clientHeight;

    const isHitBottom = bottomHeight >= e.scrollHeight - 10;

    setHitBottom(isHitBottom);
    setAutoScroll(isHitBottom);
  };

  function scrollDomToBottom() {
    const dom = scrollRef.current;
    if (dom) {
      requestAnimationFrame(() => {
        setAutoScroll(true);
        dom.scrollTo({ top: dom.scrollHeight, behavior: "auto" });
      });
    }
  }

  // auto scroll
  useEffect(() => {
    if (autoScroll) {
      scrollDomToBottom();
    }
  });

  return {
    scrollRef,
    autoScroll,
    setAutoScroll,
    scrollDomToBottom,
    hitBottom,
    setHitBottom,
    onChatBodyScroll,
  };
}
