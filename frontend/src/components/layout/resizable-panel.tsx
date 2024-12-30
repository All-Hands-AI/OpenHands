import React, { useCallback, useEffect, useState } from "react";
import { cn } from "#/utils/cn";
import ChevronLeftIcon from "#/icons/chevron-left.svg?react";
import ChevronRightIcon from "#/icons/chevron-right.svg?react";

interface ResizablePanelProps {
  children: React.ReactNode;
  leftPanel: React.ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  className?: string;
}

export function ResizablePanel({
  children,
  leftPanel,
  defaultLeftWidth = 390,
  minLeftWidth = 300,
  maxLeftWidth = 600,
  className,
}: ResizablePanelProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [previousWidth, setPreviousWidth] = useState(defaultLeftWidth);

  const handleMouseDown = useCallback(() => {
    setIsResizing(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = Math.min(
        Math.max(minLeftWidth, e.clientX),
        maxLeftWidth,
      );
      setLeftWidth(newWidth);
    },
    [isResizing, minLeftWidth, maxLeftWidth],
  );

  const toggleCollapse = useCallback(() => {
    if (isCollapsed) {
      setLeftWidth(previousWidth);
    } else {
      setPreviousWidth(leftWidth);
      setLeftWidth(0);
    }
    setIsCollapsed(!isCollapsed);
  }, [isCollapsed, leftWidth, previousWidth]);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div className={cn("flex h-full relative", className)}>
      <div
        className="h-full overflow-auto"
        style={{ width: leftWidth, minWidth: leftWidth }}
      >
        {leftPanel}
      </div>
      <div
        className="absolute h-full w-1 bg-default-200 hover:bg-primary cursor-col-resize flex items-center justify-center"
        style={{ left: leftWidth }}
        onMouseDown={handleMouseDown}
      >
        <button
          type="button"
          onClick={toggleCollapse}
          className="absolute z-10 -right-3 top-1/2 -translate-y-1/2 bg-default-100 hover:bg-default-200 rounded-full p-1 border border-default-200"
        >
          {isCollapsed ? (
            <ChevronRightIcon className="w-4 h-4" />
          ) : (
            <ChevronLeftIcon className="w-4 h-4" />
          )}
        </button>
      </div>
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
