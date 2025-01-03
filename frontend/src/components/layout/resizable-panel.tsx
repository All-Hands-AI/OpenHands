import React, {
  CSSProperties,
  JSX,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  VscChevronDown,
  VscChevronLeft,
  VscChevronRight,
  VscChevronUp,
} from "react-icons/vsc";
import { twMerge } from "tailwind-merge";
import { IconButton } from "../shared/buttons/icon-button";

export enum Orientation {
  HORIZONTAL = "horizontal",
  VERTICAL = "vertical",
}

enum Collapse {
  COLLAPSED = "collapsed",
  SPLIT = "split",
  FILLED = "filled",
}

type ResizablePanelProps = {
  firstChild: React.ReactNode;
  firstClassName: string | undefined;
  secondChild: React.ReactNode;
  secondClassName: string | undefined;
  className: string | undefined;
  orientation: Orientation;
  initialSize: number;
};

export function ResizablePanel({
  firstChild,
  firstClassName,
  secondChild,
  secondClassName,
  className,
  orientation,
  initialSize,
}: ResizablePanelProps): JSX.Element {
  const [firstSize, setFirstSize] = useState<number>(() => {
    // Enforce initial size constraints
    if (orientation === Orientation.HORIZONTAL) {
      const minWidth = 350;
      const maxWidth = window.innerWidth * 0.3;
      return Math.min(Math.max(initialSize, minWidth), maxWidth);
    }
    const minHeight = 250;
    const maxHeight = window.innerHeight * 0.7;
    return Math.min(Math.max(initialSize, minHeight), maxHeight);
  });
  const [dividerPosition, setDividerPosition] = useState<number | null>(null);
  const firstRef = useRef<HTMLDivElement>(null);
  const secondRef = useRef<HTMLDivElement>(null);
  const [collapse, setCollapse] = useState<Collapse>(Collapse.SPLIT);
  const isHorizontal = orientation === Orientation.HORIZONTAL;

  // Debounce function to limit resize handler calls
  const debounce = useCallback((fn: () => void, delay: number) => {
    let timeoutId: NodeJS.Timeout;
    return () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(fn, delay);
    };
  }, []);

  // Handle window resize to maintain constraints
  useEffect(() => {
    const handleResize = () => {
      if (orientation === Orientation.HORIZONTAL) {
        const maxWidth = Math.min(
          window.innerWidth * 0.5, // Max 50% of window width
          window.innerWidth - 600, // Leave at least 600px for second panel
        );
        const minWidth = 350;
        const newSize = Math.min(Math.max(firstSize, minWidth), maxWidth);
        if (newSize !== firstSize) {
          setFirstSize(newSize);
        }
      } else {
        const maxHeight = window.innerHeight * 0.7;
        const minHeight = 300; // Match terminal's minHeight
        const newSize = Math.min(Math.max(firstSize, minHeight), maxHeight);
        if (newSize !== firstSize) {
          setFirstSize(newSize);
        }
      }
    };

    // Initial resize to ensure proper sizing
    handleResize();

    const debouncedResize = debounce(handleResize, 100);
    window.addEventListener("resize", debouncedResize);
    return () => window.removeEventListener("resize", debouncedResize);
  }, [orientation, firstSize, debounce]);

  useEffect(() => {
    if (dividerPosition == null || !firstRef.current) {
      return undefined;
    }
    const getFirstSizeFromEvent = (e: MouseEvent) => {
      const position = isHorizontal ? e.clientX : e.clientY;
      const newSize = firstSize + position - dividerPosition;

      // Enforce min/max constraints
      if (isHorizontal) {
        const minWidth = 350; // Min width for chat panel
        const maxWidth = Math.min(
          window.innerWidth * 0.5, // Max 50% of window width
          window.innerWidth - 600, // Leave at least 600px for second panel
        );
        return Math.min(Math.max(newSize, minWidth), maxWidth);
      }
      const minHeight = 300; // Min height for workspace/terminal panel
      const maxHeight = window.innerHeight * 0.7; // 70% of window height
      return Math.min(Math.max(newSize, minHeight), maxHeight);
    };
    const onMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const newFirstSize = `${getFirstSizeFromEvent(e)}px`;
      const { current } = firstRef;
      if (current) {
        if (isHorizontal) {
          current.style.width = newFirstSize;
          current.style.minWidth = newFirstSize;
        } else {
          current.style.height = newFirstSize;
          current.style.minHeight = newFirstSize;
        }
      }
    };
    const onMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      if (firstRef.current) {
        firstRef.current.style.transition = "";
      }
      if (secondRef.current) {
        secondRef.current.style.transition = "";
      }
      setFirstSize(getFirstSizeFromEvent(e));
      setDividerPosition(null);
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [dividerPosition, firstSize, orientation]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    if (firstRef.current) {
      firstRef.current.style.transition = "none";
    }
    if (secondRef.current) {
      secondRef.current.style.transition = "none";
    }
    const position = isHorizontal ? e.clientX : e.clientY;
    setDividerPosition(position);
  };

  const getStyleForFirst = useCallback(() => {
    const style: CSSProperties = { overflow: "hidden" };
    if (collapse === Collapse.COLLAPSED) {
      style.opacity = 0;
      style.width = 0;
      style.minWidth = 0;
      style.height = 0;
      style.minHeight = 0;
    } else if (collapse === Collapse.SPLIT) {
      if (isHorizontal) {
        const minWidth = 350;
        const maxWidth = Math.min(
          window.innerWidth * 0.5,
          window.innerWidth - 600,
        );
        // Ensure first panel width respects min/max constraints
        const width = Math.min(Math.max(firstSize, minWidth), maxWidth);
        style.width = `${width}px`;
        style.minWidth = `${minWidth}px`;
        style.maxWidth = "50%"; // Allow chat panel to expand up to 50%
      } else {
        const minHeight = 250;
        const maxHeight = window.innerHeight * 0.7;
        // Ensure first panel height respects min/max constraints
        const height = Math.min(Math.max(firstSize, minHeight), maxHeight);
        style.height = `${height}px`;
        style.minHeight = `${minHeight}px`;
        style.maxHeight = "70%";
      }
    } else {
      style.flexGrow = 1;
    }
    return style;
  }, [collapse, firstSize, isHorizontal]);

  const getStyleForSecond = useCallback(() => {
    const style: CSSProperties = { overflow: "hidden" };
    if (collapse === Collapse.FILLED) {
      style.opacity = 0;
      style.width = 0;
      style.minWidth = 0;
      style.height = 0;
      style.minHeight = 0;
    } else if (collapse === Collapse.SPLIT) {
      if (isHorizontal) {
        // Calculate remaining width after first panel
        const remainingWidth = window.innerWidth - firstSize;
        const minWidth = 600;
        const maxWidth = window.innerWidth - Math.max(firstSize, 350); // Ensure it doesn't exceed window width

        // Ensure second panel width respects min/max constraints
        const width = Math.min(Math.max(remainingWidth, minWidth), maxWidth);
        style.width = `${width}px`;
        style.minWidth = `${minWidth}px`;
        style.flexGrow = 1; // Allow second panel to grow and fill remaining space
      } else {
        // Calculate remaining height after first panel
        const remainingHeight = window.innerHeight - firstSize;
        const minHeight = 300;
        const maxHeight = window.innerHeight * 0.7;

        // Ensure second panel height respects min/max constraints
        const height = Math.min(
          Math.max(remainingHeight, minHeight),
          maxHeight,
        );
        style.height = `${height}px`;
        style.minHeight = `${minHeight}px`;
        style.maxHeight = "70%";
        style.flexGrow = 1; // Allow terminal to grow vertically
        style.display = "flex"; // Enable flex layout for terminal
        style.flexDirection = "column"; // Stack terminal content vertically
      }
    } else {
      style.flexGrow = 1;
    }
    return style;
  }, [collapse, firstSize, isHorizontal]);

  const onCollapse = () => {
    if (collapse === Collapse.SPLIT) {
      setCollapse(Collapse.COLLAPSED);
    } else {
      setCollapse(Collapse.SPLIT);
    }
  };

  const onExpand = () => {
    if (collapse === Collapse.SPLIT) {
      setCollapse(Collapse.FILLED);
    } else {
      setCollapse(Collapse.SPLIT);
    }
  };

  return (
    <div className={twMerge("flex", !isHorizontal && "flex-col", className)}>
      <div
        ref={firstRef}
        className={twMerge(firstClassName, "transition-all ease-soft-spring")}
        style={getStyleForFirst()}
      >
        {firstChild}
      </div>
      <div
        className={`${isHorizontal ? "cursor-ew-resize w-3 flex-col" : "cursor-ns-resize h-3 flex-row"} shrink-0 flex justify-center items-center`}
        onMouseDown={collapse === Collapse.SPLIT ? onMouseDown : undefined}
      >
        <IconButton
          icon={isHorizontal ? <VscChevronLeft /> : <VscChevronUp />}
          ariaLabel="Collapse"
          onClick={onCollapse}
        />
        <IconButton
          icon={isHorizontal ? <VscChevronRight /> : <VscChevronDown />}
          ariaLabel="Expand"
          onClick={onExpand}
        />
      </div>
      <div
        ref={secondRef}
        className={twMerge(secondClassName, "transition-all ease-soft-spring")}
        style={getStyleForSecond()}
      >
        {secondChild}
      </div>
    </div>
  );
}
