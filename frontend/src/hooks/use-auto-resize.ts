import { useCallback, useEffect, RefObject, useRef } from "react";
import { IMessageToSend } from "#/state/conversation-slice";
import { useCallback, useEffect, RefObject } from "react";
import { IMessageToSend } from "#/state/conversation-store";
import { useDragResize } from "./use-drag-resize";

// Constants
const DEFAULT_MIN_HEIGHT = 20;
const DEFAULT_MAX_HEIGHT = 120;
const HEIGHT_INCREMENT = 20;
const MANUAL_OVERSIZE_THRESHOLD = 50;

// ------- Debug & helpers -------
const DEBUG_RESIZE = false; // toggle to true while debugging
const dbg = (...args: unknown[]) => {
  if (DEBUG_RESIZE) console.log("[resize]", ...args);
};

const EPS = 1.5; // px tolerance for "near min"

const getStyleHeightPx = (el: HTMLElement, fallback: number) => {
  const h = parseFloat(el.style.height || "");
  return Number.isFinite(h) ? h : fallback;
};

const setStyleHeightPx = (el: HTMLElement, h: number) => {
  // eslint-disable-next-line no-param-reassign
  el.style.height = `${h}px`;
};

// Track user's manual intent & exact height
const useManualHeight = () => {
  const hasUserResizedRef = useRef(false);
  const manualHeightRef = useRef<number | null>(null);
  return { hasUserResizedRef, manualHeightRef };
};

// -------------------------------

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
  enableManualResize?: boolean;
  onGripDragStart?: () => void;
  onGripDragEnd?: () => void;
  onHeightChange?: (height: number) => void; // New callback for height changes
  value?: IMessageToSend;
}

interface UseAutoResizeReturn {
  autoResize: () => void;
  smartResize: () => void;
  handleGripMouseDown: (e: React.MouseEvent) => void;
  handleGripTouchStart: (e: React.TouchEvent) => void;
  increaseHeightForEmptyContent: () => void;
  resetManualResize: () => void;
}

// Height management utilities
interface HeightConstraints {
  minHeight: number;
  maxHeight: number;
}

interface HeightMeasurements {
  currentHeight: number;
  currentStyleHeight: number;
  contentHeight: number;
}

interface ResizeStrategy {
  finalHeight: number;
  overflowY: "hidden" | "auto";
}

const applyHeightToElement = (
  element: HTMLElement,
  height: number,
  constraints: HeightConstraints,
): number => {
  const { minHeight, maxHeight } = constraints;
  const finalHeight = Math.max(minHeight, Math.min(height, maxHeight));

  element.style.setProperty("height", `${finalHeight}px`);
  element.style.setProperty(
    "overflow-y",
    finalHeight >= maxHeight ? "auto" : "hidden",
  );

  return finalHeight;
};

const calculateOptimalHeight = (
  element: HTMLElement,
  constraints: HeightConstraints,
): number => {
  const { minHeight, maxHeight, scrollHeight } = {
    ...constraints,
    scrollHeight: element.scrollHeight,
  };

  if (scrollHeight <= maxHeight) {
    return Math.max(scrollHeight, minHeight);
  }
  return maxHeight;
};

// Removed unused function

const isManuallyOversized = (
  currentHeight: number,
  contentHeight: number,
  threshold = MANUAL_OVERSIZE_THRESHOLD,
): boolean => currentHeight > contentHeight + threshold;

const measureElementHeights = (
  element: HTMLElement,
  minHeight: number,
): HeightMeasurements => {
  // Use the previous explicit style height as the "current" for restore, not offsetHeight
  const currentStyleHeight = getStyleHeightPx(element, minHeight);
  const currentHeight = currentStyleHeight;

  // Temporarily reset to measure content
  element.style.setProperty("height", "auto");
  const contentHeight = element.scrollHeight;

  // Restore height
  setStyleHeightPx(element, currentStyleHeight);

  return {
    currentHeight,
    currentStyleHeight,
    contentHeight,
  };
};

const applyResizeStrategy = (
  element: HTMLElement,
  strategy: ResizeStrategy,
): void => {
  const { finalHeight, overflowY } = strategy;
  const elementRef = element;
  elementRef.style.height = `${finalHeight}px`;
  elementRef.style.overflowY = overflowY;
};

const executeHeightCallback = (
  height: number,
  onHeightChange?: (height: number) => void,
): void => {
  if (onHeightChange) {
    onHeightChange(height);
  }
};

// DOM manipulation utilities
const resetElementHeight = (element: HTMLElement): void => {
  element.style.setProperty("height", "auto");
  element.style.setProperty("overflow-y", "hidden");
};

export const useAutoResize = (
  elementRef: RefObject<HTMLElement | null>,
  options: UseAutoResizeOptions = {},
): UseAutoResizeReturn => {
  const {
    minHeight = DEFAULT_MIN_HEIGHT,
    maxHeight = DEFAULT_MAX_HEIGHT,
    enableManualResize = false,
    value,
    onGripDragStart,
    onGripDragEnd,
    onHeightChange,
  } = options;

  const constraints: HeightConstraints = { minHeight, maxHeight };
  const { hasUserResizedRef, manualHeightRef } = useManualHeight();

  const resetManualResize = () => {
    hasUserResizedRef.current = false;
    manualHeightRef.current = null;
    dbg("manual reset");
  };

  // Wrap onHeightChange so we can remember user-chosen manual height during drag
  const handleExternalHeightChange = useCallback(
    (h: number) => {
      onHeightChange?.(h);
      if (hasUserResizedRef.current) {
        manualHeightRef.current = h;
        dbg("manual height set", h);
      }
    },
    [onHeightChange],
  );

  // Use the drag resize hook for manual resizing functionality
  const { handleGripMouseDown, handleGripTouchStart } = useDragResize({
    elementRef,
    minHeight,
    maxHeight,
    onGripDragStart: enableManualResize
      ? () => {
          hasUserResizedRef.current = true;
          dbg("manual start");
          onGripDragStart?.();
        }
      : undefined,
    onGripDragEnd: enableManualResize
      ? () => {
          // Check if we're at minimum height and clear manual mode if so
          const element = elementRef.current;
          if (element) {
            const currentHeight = getStyleHeightPx(element, minHeight);
            if (Math.abs(currentHeight - minHeight) <= EPS) {
              hasUserResizedRef.current = false;
              manualHeightRef.current = null;
              dbg("manual cleared at min on drag end");
            }
          }
          onGripDragEnd?.();
        }
      : undefined,
    onHeightChange: handleExternalHeightChange,
    onReachedMinHeight: () => {
      // Don't clear manual mode during drag - only clear on drag end
      dbg("reached min height during drag");
    },
  });

  // Auto-resize functionality for contenteditable div
  const autoResize = () => {
    const element = elementRef.current;
    if (!element) return;

    // Reset height to auto to get the actual content height
    resetElementHeight(element);

    // Calculate and apply optimal height
    const optimalHeight = calculateOptimalHeight(element, constraints);
    const finalHeight = applyHeightToElement(
      element,
      optimalHeight,
      constraints,
    );

    // Execute height change callback
    executeHeightCallback(finalHeight, onHeightChange);
  };

  // Handle content that fits within current height
  const handleContentFitsInCurrentHeight = useCallback(
    (element: HTMLElement, currentHeight: number, contentHeight: number) => {
      // If user manually resized and we're above min height, preserve their chosen height
      if (hasUserResizedRef.current && currentHeight > minHeight) {
        applyResizeStrategy(element, {
          finalHeight: currentHeight,
          overflowY: "hidden",
        });
        executeHeightCallback(currentHeight, onHeightChange);
        return true;
      }

      // Otherwise allow shrinking towards content (respect minHeight)
      const finalHeight = Math.max(contentHeight, minHeight);
      applyResizeStrategy(element, {
        finalHeight,
        overflowY: "hidden",
      });
      executeHeightCallback(finalHeight, onHeightChange);
      return true;
    },
    [minHeight, onHeightChange],
  );

  // Handle content that exceeds current height but within max height
  const handleContentExceedsCurrentHeight = useCallback(
    (element: HTMLElement, currentHeight: number, contentHeight: number) => {
      // Grow unless the element is manually oversized beyond content significantly
      if (!isManuallyOversized(currentHeight, contentHeight)) {
        const finalHeight = Math.max(contentHeight, minHeight);
        applyResizeStrategy(element, {
          finalHeight,
          overflowY: "hidden",
        });
        executeHeightCallback(finalHeight, onHeightChange);
        return true;
      }

      // Keep manual height and allow scrolling as needed
      applyResizeStrategy(element, {
        finalHeight: currentHeight,
        overflowY: "auto",
      });
      executeHeightCallback(currentHeight, onHeightChange);
      return true;
    },
    [minHeight, onHeightChange],
  );

  // Handle content that exceeds max height
  const handleContentExceedsMaxHeight = useCallback(
    (element: HTMLElement) => {
      applyResizeStrategy(element, {
        finalHeight: maxHeight,
        overflowY: "auto",
      });
      executeHeightCallback(maxHeight, onHeightChange);
    },
    [maxHeight, onHeightChange],
  );

  // Debounced smartResize body
  const smartResizeBody = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    const textIsEmpty = (element.textContent ?? "").trim().length === 0;
    const styleH = getStyleHeightPx(element, minHeight);
    dbg("SMART start", {
      manual: hasUserResizedRef.current,
      manualHeight: manualHeightRef.current,
      styleHeight: styleH,
      textLen: (element.textContent ?? "").length,
    });

    // If empty content and we have a manual height above min, preserve it
    if (
      textIsEmpty &&
      hasUserResizedRef.current &&
      manualHeightRef.current &&
      manualHeightRef.current > minHeight + EPS
    ) {
      setStyleHeightPx(element, manualHeightRef.current);
      element.style.overflowY = "hidden";
      executeHeightCallback(manualHeightRef.current, onHeightChange);
      dbg("PRESERVE manual on empty", manualHeightRef.current);
      return;
    }

    // Measure element heights
    const measurements = measureElementHeights(element, minHeight);
    const { currentHeight, contentHeight } = measurements;

    // If content fits within current height
    if (contentHeight <= currentHeight) {
      handleContentFitsInCurrentHeight(element, currentHeight, contentHeight);
      return;
    }

    // If content exceeds current height but within max
    if (contentHeight <= maxHeight) {
      handleContentExceedsCurrentHeight(element, currentHeight, contentHeight);
      return;
    }

    // Content exceeds max height
    handleContentExceedsMaxHeight(element);
  }, [elementRef, minHeight, maxHeight, onHeightChange]);

  // rAF-debounced smartResize wrapper to collapse bursts
  const pendingSmartRef = useRef<number | null>(null);
  const smartResize = useCallback(() => {
    if (pendingSmartRef.current) cancelAnimationFrame(pendingSmartRef.current);
    pendingSmartRef.current = requestAnimationFrame(() => {
      pendingSmartRef.current = null;
      smartResizeBody();
    });
  }, [smartResizeBody]);

  // Function to increase height when content is empty
  const increaseHeightForEmptyContent = () => {
    const element = elementRef.current;
    if (!element) return;

    const currentHeight = getStyleHeightPx(element, minHeight);
    const newHeight = Math.min(currentHeight + HEIGHT_INCREMENT, maxHeight);

    if (newHeight > currentHeight) {
      const finalHeight = applyHeightToElement(element, newHeight, constraints);

      // Execute height change callback
      executeHeightCallback(finalHeight, onHeightChange);
    }
  };

  // Update content and resize when value prop changes
  useEffect(() => {
    const element = elementRef.current;
    if (element && value !== undefined) {
      element.textContent = value.text;
      smartResize();
    }
  }, [value, smartResize]);

  // Initialize auto-resize on mount
  useEffect(() => {
    smartResize();
  }, [smartResize]);

  return {
    autoResize,
    smartResize,
    handleGripMouseDown,
    handleGripTouchStart,
    increaseHeightForEmptyContent,
    resetManualResize,
  };
};
