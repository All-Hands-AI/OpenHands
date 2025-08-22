import { useEffect, useCallback, useRef } from "react";

interface UseTrackElementWidthProps {
  elementRef: React.RefObject<HTMLElement | null>;
  callback: (width: number) => void;
  delay?: number; // Optional delay parameter with default
}

export const useTrackElementWidth = ({
  elementRef,
  callback,
  delay = 100, // Default 100ms delay
}: UseTrackElementWidthProps) => {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Create debounced callback that only fires after delay
  const debouncedCallback = useCallback(
    (width: number) => {
      // Clear existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set new timeout
      timeoutRef.current = setTimeout(() => {
        callback(width);
      }, delay);
    },
    [callback, delay],
  );

  useEffect(() => {
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        debouncedCallback(entry.contentRect.width);
      }
    });

    if (elementRef.current) {
      resizeObserver.observe(elementRef.current);
    }

    return () => {
      // Clean up timeout and observer
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      resizeObserver.disconnect();
    };
  }, [debouncedCallback]);
};
