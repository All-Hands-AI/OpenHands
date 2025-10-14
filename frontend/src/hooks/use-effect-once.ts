import React from "react";

// Introduce this custom React hook to run any given effect
// ONCE. In Strict mode, React will run all useEffect's twice,
// which will trigger a WebSocket connection and then immediately
// close it, causing the "closed before could connect" error.
export const useEffectOnce = (callback: () => void | (() => void)) => {
  const isUsedRef = React.useRef<boolean>(false);
  const cleanupRef = React.useRef<(() => void) | void>(undefined);
  const isMountedRef = React.useRef<boolean>(true);

  React.useEffect(() => {
    if (isUsedRef.current) {
      // Already ran the effect, but this is a remount (likely Strict Mode)
      // Reset the mounted flag
      isMountedRef.current = true;
      return undefined;
    }

    isUsedRef.current = true;
    isMountedRef.current = true;
    cleanupRef.current = callback();

    return () => {
      // Only run cleanup if the component is actually being unmounted,
      // not during Strict Mode's double-invoke
      if (isMountedRef.current) {
        isMountedRef.current = false;
        // Wait a tick to see if we remount (Strict Mode behavior)
        setTimeout(() => {
          if (
            !isMountedRef.current &&
            typeof cleanupRef.current === "function"
          ) {
            cleanupRef.current();
          }
        }, 0);
      }
    };
  }, []);
};
