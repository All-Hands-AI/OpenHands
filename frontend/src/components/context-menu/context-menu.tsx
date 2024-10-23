import React from "react";
import { cn } from "#/utils/utils";

interface ContextMenuProps {
  testId?: string;
  children: React.ReactNode;
  className?: React.HTMLAttributes<HTMLUListElement>["className"];
}

export const ContextMenu = React.forwardRef<HTMLUListElement, ContextMenuProps>(
  ({ testId, children, className }, ref) => (
    <ul
      data-testid={testId}
      ref={ref}
      className={cn("bg-[#404040] rounded-md w-[224px]", className)}
    >
      {children}
    </ul>
  ),
);

ContextMenu.displayName = "ContextMenu";
