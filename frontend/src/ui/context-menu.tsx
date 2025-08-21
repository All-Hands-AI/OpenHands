import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "#/utils/utils";

const contextMenuVariants = cva(
  "absolute bg-tertiary rounded-[6px] text-white overflow-hidden z-50 shadow-[0_10px_15px_-3px_rgba(0,0,0,0.10),0_4px_6px_-2px_rgba(0,0,0,0.05),0_0_0_1px_rgba(0,0,0,0.05)]",
  {
    variants: {
      size: {
        compact: "py-1 px-1",
        default: "py-[6px] px-1",
        wide: "py-2 px-2",
      },
      layout: {
        vertical: "flex flex-col gap-2",
        horizontal: "flex flex-row gap-2",
      },
      position: {
        top: "bottom-full",
        bottom: "top-full",
        left: "right-full",
        right: "left-full",
      },
      spacing: {
        tight: "mt-1",
        default: "mt-2",
        loose: "mt-3",
      },
      alignment: {
        left: "left-0",
        right: "right-0",
        center: "left-1/2 transform -translate-x-1/2",
      },
    },
    defaultVariants: {
      size: "default",
      layout: "vertical",
      spacing: "default",
    },
  },
);

interface ContextMenuProps {
  ref?: React.RefObject<HTMLUListElement | null>;
  testId?: string;
  children: React.ReactNode;
  className?: React.HTMLAttributes<HTMLUListElement>["className"];
  size?: VariantProps<typeof contextMenuVariants>["size"];
  layout?: VariantProps<typeof contextMenuVariants>["layout"];
  position?: VariantProps<typeof contextMenuVariants>["position"];
  spacing?: VariantProps<typeof contextMenuVariants>["spacing"];
  alignment?: VariantProps<typeof contextMenuVariants>["alignment"];
}

export function ContextMenu({
  testId,
  children,
  className,
  ref,
  size,
  layout,
  position,
  spacing,
  alignment,
}: ContextMenuProps) {
  return (
    <ul
      data-testid={testId}
      ref={ref}
      className={cn(
        contextMenuVariants({ size, layout, position, spacing, alignment }),
        className,
      )}
    >
      {children}
    </ul>
  );
}
