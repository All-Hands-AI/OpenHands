import type { PropsWithChildren } from "react";
import type { BaseProps, HTMLProps } from "../../../shared/types";
import { cn } from "../../../shared/utils/cn";

export type AccordionPanelProps = Omit<HTMLProps<"div">, "aria-expanded"> & {
  expanded: boolean;
} & BaseProps;

export const AccordionPanel = ({
  className,
  children,
  expanded,
  ...props
}: PropsWithChildren<AccordionPanelProps>) => {
  return (
    <div
      aria-expanded={expanded}
      className={cn(
        "px-6 py-4",
        "ring-1 ring-solid ring-light-neutral-500 bg-grey-800",
        "rounded-b-2xl",
        "aria-[expanded=false]:hidden",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
