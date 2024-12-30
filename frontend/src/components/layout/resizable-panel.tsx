import React, { useCallback, useEffect, useState } from "react";
import { cn } from "#/utils/cn";
import ChevronLeftIcon from "#/icons/chevron-left";
import ChevronRightIcon from "#/icons/chevron-right";

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
        className={cn(
          "h-full overflow-auto transition-[width] duration-300 ease-in-out",
          isCollapsed && "w-0 min-w-0"
        )}
        style={!isCollapsed ? { width: leftWidth, minWidth: leftWidth } : undefined}
      >
        {leftPanel}
      </div>
      <div
        className={cn(
          "absolute h-full w-1 bg-gray-200 hover:bg-blue-500 cursor-col-resize flex items-center justify-center transition-[left,background-color] duration-300 ease-in-out",
          isCollapsed && "left-0"
        )}
        style={!isCollapsed ? { left: leftWidth } : undefined}
        onMouseDown={handleMouseDown}
      >
        <button
          type="button"
          onClick={toggleCollapse}
          className="absolute z-10 -right-3 top-1/2 -translate-y-1/2 bg-white hover:bg-gray-100 rounded-full p-1 border border-gray-200 shadow-sm transition-colors duration-200"
        >
          {isCollapsed ? (
            <ChevronRightIcon className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronLeftIcon className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </div>
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
