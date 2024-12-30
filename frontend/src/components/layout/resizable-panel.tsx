import React, { useCallback, useEffect, useState } from "react";
import { cn } from "#/lib/utils";

interface ResizablePanelProps {
  leftPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
  className?: string;
}

export function ResizablePanel({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 390,
  minLeftWidth = 280,
  maxLeftWidth = 600,
  className,
}: ResizablePanelProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (e: MouseEvent) => {
      if (isResizing) {
        const newWidth = e.clientX;
        if (newWidth >= minLeftWidth && newWidth <= maxLeftWidth) {
          setLeftWidth(newWidth);
        }
      }
    },
    [isResizing, minLeftWidth, maxLeftWidth],
  );

  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResizing);
    }

    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={cn("flex h-full overflow-auto gap-3", className)}>
      <div
        style={{ width: isCollapsed ? "40px" : `${leftWidth}px` }}
        className="transition-width duration-200 ease-in-out"
      >
        {leftPanel}
      </div>
      <div
        className="flex items-center cursor-col-resize select-none"
        onMouseDown={startResizing}
        onClick={toggleCollapse}
      >
        <div className="w-3 h-16 hover:bg-gray-200 dark:hover:bg-gray-700 rounded flex items-center justify-center">
          <div className="w-0.5 h-8 bg-gray-300 dark:bg-gray-600" />
        </div>
      </div>
      <div className="flex-grow">{rightPanel}</div>
    </div>
  );
}