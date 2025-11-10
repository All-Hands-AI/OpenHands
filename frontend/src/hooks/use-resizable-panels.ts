import { useState, useRef, useCallback, useEffect } from "react";
import { useLocalStorage } from "@uidotdev/usehooks";

interface UseResizablePanelsOptions {
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  storageKey?: string;
}

export function useResizablePanels({
  defaultLeftWidth = 50,
  minLeftWidth = 30,
  maxLeftWidth = 80,
  storageKey = "desktop-layout-panel-width",
}: UseResizablePanelsOptions = {}) {
  const [persistedWidth, setPersistedWidth] = useLocalStorage<number>(
    storageKey,
    defaultLeftWidth,
  );

  const [leftWidth, setLeftWidth] = useState(persistedWidth);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const clampWidth = useCallback(
    (width: number) => Math.max(minLeftWidth, Math.min(maxLeftWidth, width)),
    [minLeftWidth, maxLeftWidth],
  );

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const mouseX = e.clientX - containerRect.left;
      const containerWidth = containerRect.width;
      const newLeftWidth = (mouseX / containerWidth) * 100;

      const clampedWidth = clampWidth(newLeftWidth);
      setLeftWidth(clampedWidth);
    },
    [isDragging, clampWidth],
  );

  const handleMouseUp = useCallback(() => {
    if (isDragging) {
      setIsDragging(false);
      setPersistedWidth(leftWidth);
    }
  }, [isDragging, leftWidth, setPersistedWidth]);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "ew-resize";
      document.body.style.userSelect = "none";
    }

    return () => {
      if (isDragging) {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const rightWidth = 100 - leftWidth;

  return {
    leftWidth,
    rightWidth,
    isDragging,
    containerRef,
    handleMouseDown,
  };
}
