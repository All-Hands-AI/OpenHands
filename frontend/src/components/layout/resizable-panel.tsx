import React, { useCallback, useEffect, useState } from "react";
import { cn } from "#/utils/cn";
import ChevronLeftIcon from "#/icons/chevron-left";
import ChevronRightIcon from "#/icons/chevron-right";

interface ResizablePanelProps {
  children: React.ReactNode;
  leftPanel: React.ReactNode;
  defaultRightWidth?: number;
  minRightWidth?: number;
  maxRightWidth?: number;
  className?: string;
}

export function ResizablePanel({
  children,
  leftPanel,
  defaultRightWidth = 390,
  minRightWidth = 300,
  maxRightWidth = 600,
  className,
}: ResizablePanelProps) {
  const [rightWidth, setRightWidth] = useState(defaultRightWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [previousWidth, setPreviousWidth] = useState(defaultRightWidth);

  const handleMouseDown = useCallback(() => {
    setIsResizing(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing) return;

      const containerWidth = window.innerWidth;
      const fromRight = containerWidth - e.clientX;
      const newWidth = Math.min(
        Math.max(minRightWidth, fromRight),
        maxRightWidth,
      );
      setRightWidth(newWidth);
    },
    [isResizing, minRightWidth, maxRightWidth],
  );

  const toggleCollapse = useCallback(() => {
    if (isCollapsed) {
      setRightWidth(previousWidth);
    } else {
      setPreviousWidth(rightWidth);
      setRightWidth(0);
    }
    setIsCollapsed(!isCollapsed);
  }, [isCollapsed, rightWidth, previousWidth]);

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
    <div className={cn("flex h-full w-full relative", className)}>
      <div className="flex-1 overflow-auto">{leftPanel}</div>
      <div
        className={cn(
          "absolute h-full w-1 bg-gray-200 hover:bg-blue-500 cursor-col-resize flex items-center justify-center transition-[right,background-color] duration-300 ease-in-out",
          isCollapsed && "right-0"
        )}
        style={!isCollapsed ? { right: rightWidth } : undefined}
        onMouseDown={handleMouseDown}
      >
        <button
          type="button"
          onClick={toggleCollapse}
          className="absolute z-10 -left-3 top-1/2 -translate-y-1/2 bg-white hover:bg-gray-100 rounded-full p-1 border border-gray-200 shadow-sm transition-colors duration-200"
        >
          {isCollapsed ? (
            <ChevronLeftIcon className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </div>
      <div
        className={cn(
          "h-full overflow-auto transition-[width] duration-300 ease-in-out",
          isCollapsed && "w-0 min-w-0"
        )}
        style={!isCollapsed ? { width: rightWidth, minWidth: rightWidth } : undefined}
      >
        {children}
      </div>
    </div>
  );
}
