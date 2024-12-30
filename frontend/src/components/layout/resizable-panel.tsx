import React, { useCallback, useEffect, useState } from "react";
import { cn } from "#/utils/cn";

interface ResizablePanelProps {
  leftPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
}

export function ResizablePanel({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 390,
  minLeftWidth = 300,
  maxLeftWidth = 600,
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
    <div className="flex h-full overflow-auto gap-3">
      <div
        style={{ width: isCollapsed ? "0px" : `${leftWidth}px` }}
        className={cn(
          "transition-[width] duration-200",
          isCollapsed && "w-0 overflow-hidden",
        )}
      >
        {leftPanel}
      </div>

      <div
        className="relative flex items-center cursor-col-resize select-none"
        onMouseDown={startResizing}
        onClick={toggleCollapse}
      >
        <div className="w-3 h-16 hover:bg-default-100 rounded-full flex items-center justify-center">
          <div className="w-0.5 h-6 bg-default-200" />
        </div>
      </div>

      <div className="flex-1 min-w-0">{rightPanel}</div>
    </div>
  );
}
