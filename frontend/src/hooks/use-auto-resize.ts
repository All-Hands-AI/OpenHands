import { useCallback, useEffect, RefObject } from "react";
import { IMessageToSend } from "#/state/conversation-store";
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

const determineResizeStrategy = (
  measurements: HeightMeasurements,
  minHeight: number,
  maxHeight: number,
): ResizeStrategy => {
  const { currentHeight, contentHeight } = measurements;

  // If content fits in current height, just manage overflow
  if (contentHeight <= currentHeight) {
    return {
      finalHeight: currentHeight,
      overflowY: "hidden",
    };
  }

  // If content exceeds current height but is within normal auto-resize range
  if (contentHeight <= maxHeight) {
    // Only grow if the current height is close to the content height (not manually resized much larger)
    if (!isManuallyOversized(currentHeight, contentHeight)) {
      return {
        finalHeight: Math.max(contentHeight, minHeight),
        overflowY: "hidden",
      };
    }
    // Keep manual height but show scrollbar since content exceeds visible area
    return {
      finalHeight: currentHeight,
      overflowY: "auto",
    };
  }

  // Content exceeds max height
  return {
    finalHeight: maxHeight,
    overflowY: "auto",
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

  // Use the drag resize hook for manual resizing functionality
  const { handleGripMouseDown, handleGripTouchStart } = useDragResize({
    elementRef,
    minHeight,
    maxHeight,
    onGripDragStart: enableManualResize ? onGripDragStart : undefined,
    onGripDragEnd: enableManualResize ? onGripDragEnd : undefined,
    onHeightChange,
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

  // Smart resize that respects manual height
  const smartResize = useCallback(() => {
    const element = elementRef.current;
    if (!element) return;

    // Measure element heights
    const measurements = measureElementHeights(element, minHeight);

    // Determine the best resize strategy
    const strategy = determineResizeStrategy(
      measurements,
      minHeight,
      maxHeight,
    );

    // Apply the resize strategy
    applyResizeStrategy(element, strategy);

    // Execute height change callback
    executeHeightCallback(strategy.finalHeight, onHeightChange);
  }, [elementRef, minHeight, maxHeight, onHeightChange]);

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
  };
};
