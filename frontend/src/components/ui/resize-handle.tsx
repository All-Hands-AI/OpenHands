import { cn } from "#/utils/utils";

interface ResizeHandleProps {
  onMouseDown: (e: React.MouseEvent) => void;
  className?: string;
}

export function ResizeHandle({ onMouseDown, className }: ResizeHandleProps) {
  return (
    <div
      className={cn("relative w-1 bg-transparent cursor-ew-resize", className)}
      onMouseDown={onMouseDown}
    >
      {/* Visual indicator */}
      <div className="absolute inset-y-0 left-1/2 w-0.5 -translate-x-1/2" />

      {/* Larger hit area for easier dragging */}
      <div className="absolute inset-y-0 -left-1 -right-1" />
    </div>
  );
}
