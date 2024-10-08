import React from "react";

// Introduce this custom React hook to run any given effect
// ONCE. In Strict mode, React will run all useEffect's twice,
// which will trigger a WebSocket connection and then immediately
// close it, causing the "closed before could connect" error.
export const useEffectOnce = (callback: () => void) => {
  const isUsedRef = React.useRef(false);

  React.useEffect(() => {
    if (isUsedRef.current) {
      return;
    }

    isUsedRef.current = true;
    callback();
  }, [isUsedRef.current]);
};
