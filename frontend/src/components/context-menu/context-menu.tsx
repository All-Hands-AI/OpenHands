import React from "react";
import { cn } from "#/utils/utils";

interface ContextMenuProps {
  children: React.ReactNode;
  className?: React.HTMLAttributes<HTMLUListElement>["className"];
}

export const ContextMenu = React.forwardRef<HTMLUListElement, ContextMenuProps>(
  ({ children, className }, ref) => (
    <ul
      ref={ref}
      className={cn("bg-[#404040] rounded-md w-[224px]", className)}
    >
      {children}
    </ul>
  ),
);

ContextMenu.displayName = "ContextMenu";
