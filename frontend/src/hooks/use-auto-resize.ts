import { useCallback, useEffect, RefObject, useRef } from "react";
import { IMessageToSend } from "#/state/conversation-slice";
import { useDragResize } from "./use-drag-resize";

// Constants
const DEFAULT_MIN_HEIGHT = 20;
const DEFAULT_MAX_HEIGHT = 120;
const HEIGHT_INCREMENT = 20;
const MANUAL_OVERSIZE_THRESHOLD = 50;

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

const getCurrentElementHeight = (
  element: HTMLElement,
  minHeight: number,
): number =>
  element.offsetHeight || parseInt(element.style.height || `${minHeight}`, 10);

const isManuallyOversized = (
  currentHeight: number,
  contentHeight: number,
  threshold = MANUAL_OVERSIZE_THRESHOLD,
): boolean => currentHeight > contentHeight + threshold;

const measureElementHeights = (
  element: HTMLElement,
  minHeight: number,
): HeightMeasurements => {
  const currentHeight = getCurrentElementHeight(element, minHeight);
  const currentStyleHeight = parseInt(
    element.style.height || `${minHeight}`,
    10,
  );

  // Temporarily reset to measure content
  element.style.setProperty("height", "auto");
  const contentHeight = element.scrollHeight;

  // Restore height
  element.style.setProperty("height", `${currentStyleHeight}px`);

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

  // Tracks whether the user has manually resized via the drag grip
  const hasUserResizedRef = useRef(false);

  // Use the drag resize hook for manual resizing functionality
  const { handleGripMouseDown, handleGripTouchStart } = useDragResize({
    elementRef,
    minHeight,
    maxHeight,
    onGripDragStart: enableManualResize
      ? () => {
          hasUserResizedRef.current = true;
          onGripDragStart?.();
        }
      : undefined,
    onGripDragEnd: enableManualResize
      ? () => {
          onGripDragEnd?.();
        }
      : undefined,
    onHeightChange,
    onReachedMinHeight: () => {
      // Reset manual resize when user drags to minimum height
      // This allows normal auto-shrinking behavior when at minimum height
      hasUserResizedRef.current = false;
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

  // Smart resize that respects manual height
  const smartResize = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    // Measure current and content heights
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
  }, [
    elementRef,
    minHeight,
    maxHeight,
    handleContentFitsInCurrentHeight,
    handleContentExceedsCurrentHeight,
    handleContentExceedsMaxHeight,
  ]);

  // Utility to reset manual-resize state (called after submit/clear)
  const resetManualResize = () => {
    hasUserResizedRef.current = false;
  };

  // Function to increase height when content is empty
  const increaseHeightForEmptyContent = () => {
    const element = elementRef.current;
    if (!element) return;

    const currentHeight = element.offsetHeight;
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
