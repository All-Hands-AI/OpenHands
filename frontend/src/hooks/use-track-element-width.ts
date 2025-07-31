import { useEffect } from "react";

interface UseTrackElementWidthProps {
  elementRef: React.RefObject<HTMLElement | null>;
  callback: (width: number) => void;
}

export const useTrackElementWidth = ({
  elementRef,
  callback,
}: UseTrackElementWidthProps) => {
  useEffect(() => {
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        callback(entry.contentRect.width);
      }
    });

    if (elementRef.current) {
      resizeObserver.observe(elementRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, []);
};
